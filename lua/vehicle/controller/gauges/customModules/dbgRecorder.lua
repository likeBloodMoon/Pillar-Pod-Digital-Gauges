-- This Source Code Form is subject to the terms of the MIT licence (see LICENSE).
-- Event recorder for Pillar Pod Digital Gauges.
--
-- Keeps a rolling buffer of the last few seconds of the car's readings and watches for moments worth
-- looking at afterwards: overboost, the rev limiter, overheating, hard braking, a new lateral-g high,
-- an impact, the engine stalling while moving, and engine damage the game reports. Each event keeps
-- a window of readings from before to after it, plus a short summary at its peak. Everything comes
-- from data the game simulates (electrics, the g sensors, the damage tracker, the crash energy); the
-- recorder never makes a reading up.
--
-- The Event History UI app (ui/modules/apps/PillarPodEvents) asks for the data through
-- bngApi.activeObjectLua and gets it back as a "PillarPodRecorder" UI event. Recordings are saved
-- as JSON in the BeamNG user folder, under pillar_pod_gauges/recordings/, and open in the same
-- viewer on a PC (viewer/index.html).
--
-- Loaded with require() from dbgAmbient, so there is one recorder per car even when the pillar
-- gauges and the cluster (a second instance of dbgAmbient) are both fitted; the first instance
-- that updates it drives it.

local M = {}

local FORMAT = "pillar-pod-recording"
local FORMAT_VERSION = 1

local RATE = 20                 -- samples per second in the rolling buffer and the event windows
local STEP = 1 / RATE
local PRE, POST = 5, 3          -- seconds kept before and after the moment an event starts
local POST_MAX = 15             -- an event that lasts long stops collecting after this many seconds
local MAX_EVENTS = 50           -- the oldest event is dropped after this many
local LOG_RATE = 2              -- whole-drive log, samples per second
local LOG_MAX = 7200            -- one hour of drive log
local SAVE_DIR = "pillar_pod_gauges/recordings/"

-- channels in every sample, in this order; units are SI-like so the viewer can convert them with
-- the game's own unit settings
local CH = {"t", "rpm", "boost", "speed", "throttle", "brake", "gear", "coolant", "oil", "egt", "glat", "glon", "damage"}
local UNITS = {t = "s", rpm = "rpm", boost = "kPa", speed = "m/s", throttle = "ratio", brake = "ratio", gear = "index",
               coolant = "C", oil = "C", egt = "C", glat = "g", glon = "g", damage = "kJ"}
local NCH = #CH
local IX = {}
for i, c in ipairs(CH) do IX[c] = i end

local PSI_TO_KPA = 6.894757

-- tuning: where each detector triggers
local T = {
  overboostMargin = 0.5,        -- psi over the car's wastegate limit (at least 5 % over)
  overboostHold = 0.3,
  limiterRatio = 0.985,         -- of the engine's maximum RPM
  limiterHold = 0.2,
  limiterCooldown = 8,
  coolantHot = 110, coolantRelease = 107, coolantHold = 1,
  oilHot = 130, oilRelease = 127, oilHold = 1,
  overheatCooldown = 30,
  brakeG = 0.8, brakeInput = 0.3, brakeHold = 0.25, brakeCooldown = 4,
  latG = 0.9, latGStep = 0.03, latHold = 0.3,
  impactKJ = 3, impactWindow = 0.25, impactCooldown = 2,
  stallSpeed = 2,               -- m/s
}

-- engine damage the game reports (damageTracker group "engine"), with a readable name
local DAMAGE = {
  mildOverrevDamage = "Over-rev damage (mild)",
  catastrophicOverrevDamage = "Over-rev damage (severe)",
  mildOverTorqueDamage = "Over-torque damage (mild)",
  catastrophicOverTorqueDamage = "Over-torque damage (severe)",
  engineReducedTorque = "Engine power reduced",
  engineHydrolocked = "Engine hydrolocked",
  engineLockedUp = "Engine locked up",
  engineDisabled = "Engine disabled",
  headGasketDamaged = "Head gasket damaged",
  pistonRingsDamaged = "Piston rings damaged",
  rodBearingsDamaged = "Rod bearings damaged",
  blockMelted = "Engine block melted",
  cylinderWallsMelted = "Cylinder walls melted",
  starvedOfOil = "Oil starvation",
  turbochargerDamaged = "Turbocharger damaged",
  superchargerDamaged = "Supercharger damaged",
  radiatorLeak = "Radiator leak",
  oilpanLeak = "Oil pan leak",
  inductionSystemDamaged = "Induction system damaged",
  exhaustBroken = "Exhaust broken",
}

local TITLES = {
  overboost = "OVERBOOST", limiter = "REV LIMITER", coolant = "COOLANT OVERHEAT", oil = "OIL OVERHEAT",
  braking = "HARD BRAKING", lateral = "LATERAL G", impact = "IMPACT", stall = "STALL", damage = "ENGINE DAMAGE",
}

-- ---------------------------------------------------------------- state

local owner = nil
local clock = 0                 -- seconds since the car was spawned (game time while driving)
local sampleT = 0
local logT = 0
local ring, ringN, ringHead = {}, math.floor((PRE + POST_MAX + 1) * RATE), 0
local ringFill = 0
local cur = {}                  -- the latest sample
for i = 1, NCH do cur[i] = 0 end
local gPeakRaw = 0              -- highest raw g (all axes) since the last sample, for impacts
local log = {}                  -- whole-drive log: one flat array per channel
local logN = 0
local events, nextId = {}, 1
local collecting = {}           -- events still filling their after-window
local det = {}                  -- detector state
local bestLat = 0
local damageSeen = {}
local damageHist = {}           -- {t, damage} pairs for the last impactWindow
local lastRunning, lastIgn = nil, 0
local resetsAt = {}             -- times the car was reset (markers in the log)
local startedAt = os.date("%Y-%m-%d %H:%M:%S")
local fileStamp = os.date("%Y%m%d_%H%M%S")
local dirty, saveT, savedPath = false, 0, nil
local ctxMaxBoost = 0

for i = 1, ringN do
  local s = {}
  for k = 1, NCH do s[k] = 0 end
  ring[i] = s
end
for k = 1, NCH do log[k] = {} end

local function num(x) return type(x) == "number" and x == x and x or nil end
-- rounded to what the viewer shows, which keeps the saved files small
local function q(x, step) return math.floor(x / step + 0.5) * step end

-- ---------------------------------------------------------------- sampling

local function readSample(e, egt)
  -- the game's boost electrics are in psi; the larger of turbo and supercharger, like the gauges
  local turbo, sc = num(e.turboBoost) or 0, num(e.superchargerBoost) or 0
  local boostPsi = sc > 0 and math.max(turbo, sc) or turbo
  cur[1] = q(clock, 0.001)
  cur[2] = q(num(e.rpm) or 0, 1)
  cur[3] = q(boostPsi * PSI_TO_KPA, 0.1)
  cur[4] = q(math.abs(num(e.wheelspeed) or num(e.airspeed) or 0), 0.01)
  cur[5] = q(num(e.throttle) or 0, 0.001)
  cur[6] = q(num(e.brake) or 0, 0.001)
  cur[7] = num(e.gearIndex) or 0
  cur[8] = q(num(e.watertemp) or 0, 0.1)
  cur[9] = q(num(e.oiltemp) or 0, 0.1)
  cur[10] = q(num(egt) or 0, 0.1)
  cur[11] = q((num(sensors.gx2) or num(sensors.gx) or 0) / 9.81, 0.001)
  cur[12] = q((num(sensors.gy2) or num(sensors.gy) or 0) / 9.81, 0.001)
  cur[13] = q((num(beamstate.damage) or 0) / 1000, 0.001)
end

local function pushRing()
  ringHead = ringHead % ringN + 1
  local s = ring[ringHead]
  for k = 1, NCH do s[k] = cur[k] end
  if ringFill < ringN then ringFill = ringFill + 1 end
end

-- copy the ring from time t0 on (oldest first) into a new window
local function ringFrom(t0)
  local w = {}
  for k = 1, NCH do w[k] = {} end
  local n = 0
  for i = ringFill - 1, 0, -1 do
    local s = ring[(ringHead - 1 - i) % ringN + 1]
    if s[1] >= t0 then
      n = n + 1
      for k = 1, NCH do w[k][n] = s[k] end
    end
  end
  return w, n
end

local function pushLog()
  if logN >= LOG_MAX then return end
  logN = logN + 1
  for k = 1, NCH do log[k][logN] = cur[k] end
end

-- ---------------------------------------------------------------- events

local function gearText(e)
  local g = e.gear
  if type(g) == "string" and g ~= "" then return g end
  local gi = num(e.gearIndex)
  if not gi then return "" end
  if gi < 0 then return "R" elseif gi == 0 then return "N" end
  return tostring(gi)
end

-- the readings shown in an event's summary, taken from the current sample
local function snapshot(e)
  return {rpm = cur[2], boost = cur[3], speed = cur[4], throttle = cur[5], brake = cur[6], gear = gearText(e),
          coolant = cur[8], oil = cur[9], egt = cur[10], glat = cur[11], glon = cur[12]}
end

local commit

-- an event starts collecting its window at once and shows in the list right away; a deferred one
-- (lateral g, which only counts if it beats the best of the drive) is added when it ends
local function newEvent(kind, t0, e, detail, defer)
  local ev = {id = 0, kind = kind, title = TITLES[kind] or kind, t = t0, duration = 0, detail = detail,
              peak = nil, peakUnit = nil, at = snapshot(e), done = false, keep = true}
  ev.window, ev.n = ringFrom(t0 - PRE)
  ev.until_ = t0 + POST
  ev.defer = defer
  table.insert(collecting, ev)
  if not defer then commit(ev) end
  return ev
end

commit = function(ev)
  if not ev.keep then return end
  ev.id = nextId                                   -- numbered when kept, so the list has no gaps
  nextId = nextId + 1
  table.insert(events, ev)
  if #events > MAX_EVENTS then table.remove(events, 1) end
  dirty = true
  if playerInfo and playerInfo.anyPlayerSeated and guihooks then
    guihooks.trigger("PillarPodRecorder", {kind = "new", id = ev.id, title = ev.title, t = ev.t})
  end
end

local function feedCollecting()
  for i = #collecting, 1, -1 do
    local ev = collecting[i]
    if ev.n < ringN then
      ev.n = ev.n + 1
      for k = 1, NCH do ev.window[k][ev.n] = cur[k] end
    end
    local over = ev.done and clock >= ev.until_
    if over or clock >= ev.t + POST_MAX then
      table.remove(collecting, i)
      if ev.defer then commit(ev) end
    end
  end
end

-- a detector that fires when a condition holds for a while; peakOf gives the value to track
-- A short dip (a gear change, a bump) doesn't end it: the condition has to stay off for GAP seconds.
local GAP = {default = 0.5, overboost = 2}     -- overboost: one pull through the gears is one event
local function runDetector(name, cond, hold, cooldown, e, peakOf, peakUnit, onEnd)
  local d = det[name]
  if not d then d = {on = false, since = 0, ev = nil, coolUntil = -1, lastOn = -1}; det[name] = d end
  if not cond and d.ev and clock - d.lastOn < (GAP[name] or GAP.default) then return end
  if cond then
    d.lastOn = clock
    if not d.on then d.on = true; d.since = clock end
    if not d.ev and clock - d.since >= hold and clock >= d.coolUntil then
      d.ev = newEvent(name, d.since, e, nil, onEnd ~= nil)
      d.ev.peakUnit = peakUnit
    end
    if d.ev then
      local v = peakOf()
      if d.ev.peak == nil or v > d.ev.peak then d.ev.peak = v; d.ev.at = snapshot(e) end
      d.ev.duration = clock - d.ev.t
      d.ev.until_ = math.max(d.ev.until_, clock + 1)
    end
  elseif d.on then
    d.on = false
    if d.ev then
      d.ev.duration = d.lastOn - d.ev.t
      if onEnd then onEnd(d.ev) end
      d.ev.done = true
      d.ev = nil
      d.coolUntil = clock + (cooldown or 0)
    end
  end
end

local function instantEvent(name, e, detail, peak, peakUnit)
  local ev = newEvent(name, clock, e, detail)
  ev.peak, ev.peakUnit, ev.done = peak, peakUnit, true
  return ev
end

local function detect(e)
  local rpm, boostPsi = cur[2], cur[3] / PSI_TO_KPA
  local running = (num(e.engineRunning) or 0) > 0
  local ign = num(e.ignitionLevel) or 0

  -- overboost: over the car's own wastegate limit
  local lim = ctxMaxBoost or 0
  runDetector("overboost", lim > 0 and boostPsi > lim + math.max(T.overboostMargin, lim * 0.05),
              T.overboostHold, 2, e, function() return cur[3] end, "kPa")

  -- rev limiter
  local maxR = num(e.maxrpm) or 0
  runDetector("limiter", running and maxR > 0 and rpm >= maxR * T.limiterRatio, T.limiterHold, T.limiterCooldown, e,
              function() return cur[2] end, "rpm")

  -- overheating, with a small hysteresis so it doesn't flicker on the line
  local dc = det.coolant
  local coolHot = cur[8] >= T.coolantHot or (dc and dc.on and cur[8] >= T.coolantRelease)
  runDetector("coolant", coolHot, T.coolantHold, T.overheatCooldown, e, function() return cur[8] end, "C")
  local doil = det.oil
  local oilHot = cur[9] >= T.oilHot or (doil and doil.on and cur[9] >= T.oilRelease)
  runDetector("oil", oilHot, T.oilHold, T.overheatCooldown, e, function() return cur[9] end, "C")

  -- hard braking: braking and decelerating hard
  runDetector("braking", cur[6] >= T.brakeInput and math.abs(cur[12]) >= T.brakeG and cur[4] > 3, T.brakeHold,
              T.brakeCooldown, e, function() return math.abs(cur[12]) end, "g")

  -- lateral g: kept only when it beats the best of this drive
  runDetector("lateral", math.abs(cur[11]) >= T.latG, T.latHold, 1, e, function() return math.abs(cur[11]) end, "g",
              function(ev)
                if (ev.peak or 0) > bestLat + T.latGStep then bestLat = ev.peak else ev.keep = false end
              end)

  -- impact: crash energy absorbed in a short time
  local dmg = cur[13]
  table.insert(damageHist, {clock, dmg})
  while #damageHist > 1 and clock - damageHist[1][1] > T.impactWindow do table.remove(damageHist, 1) end
  local dE = dmg - damageHist[1][2]
  local di = det.impact
  if not di then di = {coolUntil = -1}; det.impact = di end
  if di.ev then                                        -- still crashing: add up the energy, track the g peak
    di.ev.peak = dmg - di.base
    di.ev.gPeak = math.max(di.ev.gPeak, gPeakRaw)
    if dE < 0.2 then di.ev.duration = clock - di.ev.t; di.ev.until_ = clock + POST; di.ev.done = true; di.ev = nil; di.coolUntil = clock + T.impactCooldown end
  elseif dE >= T.impactKJ and clock >= di.coolUntil then
    di.base = damageHist[1][2]
    di.ev = instantEvent("impact", e, nil, dE, "kJ")
    di.ev.done = false
    di.ev.gPeak = gPeakRaw
    di.ev.speedBefore = (function()
      local w = di.ev.window
      local n = #w[1]
      local idx = math.max(1, n - math.floor(0.5 * RATE))
      return w[4][idx] or cur[4]
    end)()
  end

  -- stall: the engine stops while the ignition is on and the car is moving
  if lastRunning and not running and ign >= 2 and cur[4] > T.stallSpeed then
    instantEvent("stall", e, nil, cur[4], "m/s")
  end
  lastRunning, lastIgn = running, ign

  -- engine damage reported by the game
  if damageTracker and damageTracker.getDamage then
    for key, label in pairs(DAMAGE) do
      local v = damageTracker.getDamage("engine", key)
      local on = v and v ~= 0
      if on and not damageSeen[key] then instantEvent("damage", e, label) end
      damageSeen[key] = on and true or false
    end
  end
end

-- ---------------------------------------------------------------- public

-- called every frame by dbgAmbient.updateGFX; ctx carries what dbgAmbient already reads
function M.update(dt, who, ctx)
  if owner == nil then owner = who end
  if who ~= owner or not dt or dt <= 0 then return end
  clock = clock + dt
  ctxMaxBoost = ctx and ctx.maxBoost or 0
  local gx, gy, gz = num(sensors.gx) or 0, num(sensors.gy) or 0, num(sensors.gz) or 0
  gPeakRaw = math.max(gPeakRaw, math.sqrt(gx * gx + gy * gy + gz * gz) / 9.81)
  sampleT = sampleT + dt
  if sampleT < STEP then return end
  sampleT = sampleT % STEP
  local e = electrics.values
  readSample(e, ctx and ctx.egt)
  pushRing()
  feedCollecting()
  pcall(detect, e)
  gPeakRaw = 0
  logT = logT + STEP
  if logT >= 1 / LOG_RATE then logT = 0; pushLog() end
  -- save the recording a few seconds after something new was recorded
  if dirty then
    saveT = saveT + STEP
    if saveT >= 5 then saveT = 0; dirty = false; pcall(M.save) end
  end
end

-- the car was reset (recovered): keep the events, mark it in the log, close what was going on
function M.onReset(who)
  if who ~= owner then return end
  table.insert(resetsAt, clock)
  for _, d in pairs(det) do
    if d.ev then d.ev.done = true; d.ev = nil end
    d.on = false
  end
  damageHist, damageSeen, lastRunning = {}, {}, nil
end

function M.clear()
  events, collecting, det, bestLat, nextId, resetsAt = {}, {}, {}, 0, 1, {}
  logN = 0
  for k = 1, NCH do log[k] = {} end
  damageHist = {}
  fileStamp = os.date("%Y%m%d_%H%M%S")
  startedAt = os.date("%Y-%m-%d %H:%M:%S")
  savedPath = nil
end

local function carInfo()
  local model, config = "", ""
  if v and v.config then
    model = v.config.mainPartName or ""
    config = (v.config.partConfigFilename or ""):match("([^/]+)%.pc$") or ""
  end
  return model, config
end

local function eventOut(ev, withWindow)
  local o = {id = ev.id, kind = ev.kind, title = ev.title, t = ev.t, duration = ev.duration, detail = ev.detail,
             peak = ev.peak, peakUnit = ev.peakUnit, at = ev.at, gPeak = ev.gPeak, speedBefore = ev.speedBefore}
  if withWindow then
    local w = {}
    for k = 1, NCH do w[CH[k]] = ev.window[k] end
    o.window = w
  end
  return o
end

local function logOut(maxPoints)
  local stepN = 1
  if maxPoints and logN > maxPoints then stepN = math.ceil(logN / maxPoints) end
  local out = {}
  for k = 1, NCH do
    local src, dst = log[k], {}
    local j = 0
    for i = 1, logN, stepN do j = j + 1; dst[j] = src[i] end
    out[CH[k]] = dst
  end
  return out
end

function M.recording(withLog)
  local model, config = carInfo()
  local evs = {}
  for i, ev in ipairs(events) do evs[i] = eventOut(ev, true) end
  return {format = FORMAT, version = FORMAT_VERSION, mod = "Pillar Pod Digital Gauges",
          started = startedAt, car = model, config = config, duration = clock,
          rate = RATE, logRate = LOG_RATE, units = UNITS, channels = CH,
          events = evs, resets = resetsAt, log = withLog ~= false and logOut() or nil}
end

function M.save()
  local model = carInfo()
  local path = SAVE_DIR .. fileStamp .. "_" .. (model ~= "" and model or "car") .. ".json"
  local ok = jsonWriteFile(path, M.recording(true), false)
  if ok then savedPath = path end
  return ok and path or nil
end

-- requests from the Event History app; the answer comes back as a "PillarPodRecorder" UI event
function M.ui(what, arg)
  if not guihooks then return end
  if what == "summary" then
    local list = {}
    for i, ev in ipairs(events) do list[i] = eventOut(ev, false) end
    local model, config = carInfo()
    guihooks.trigger("PillarPodRecorder", {kind = "summary", car = model, config = config, started = startedAt,
                     duration = clock, events = list, recording = #collecting > 0, savedPath = savedPath,
                     units = UNITS, format = FORMAT, version = FORMAT_VERSION})
  elseif what == "event" then
    for _, ev in ipairs(events) do
      if ev.id == tonumber(arg) then
        guihooks.trigger("PillarPodRecorder", {kind = "event", event = eventOut(ev, true), units = UNITS})
        return
      end
    end
  elseif what == "log" then
    guihooks.trigger("PillarPodRecorder", {kind = "log", log = logOut(1500), resets = resetsAt, units = UNITS,
                     events = (function() local l = {} for i, ev in ipairs(events) do l[i] = {id = ev.id, t = ev.t, title = ev.title} end return l end)()})
  elseif what == "save" then
    local path = M.save()
    guihooks.trigger("PillarPodRecorder", {kind = "saved", path = path})
  elseif what == "clear" then
    M.clear()
    M.ui("summary")
  end
end

M.CHANNELS = CH
M.TUNING = T
return M
