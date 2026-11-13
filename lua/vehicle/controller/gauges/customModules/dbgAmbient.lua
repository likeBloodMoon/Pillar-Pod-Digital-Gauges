-- Ambient light (automatic display dimming), turbo wastegate limit (automatic LED scale),
-- exhaust gas temperature, data for the multi-function display and automatic mounting for the
-- digital pillar gauges.
-- Works as a custom module of gauges/genericGauges: it adds customModules.dbgAmbient.light to the
-- data sent to the gauge screens. 1 = full daylight, 0 = night. It asks the game engine for the
-- time of day every couple of seconds; if that fails for any reason the value simply stays at 1.

local M = {}
M.type = "auxiliary"

local light = 1
local timer = 99

local function setLight(v)
  v = tonumber(v)
  if v then
    light = math.max(0, math.min(1, v))
  end
end

local function requestLight()
  local id = obj:getID()
  local cmd = [[
    local l = 1
    local ok, tod = pcall(function() return core_environment.getTimeOfDay() end)
    if ok and type(tod) == "table" and type(tod.time) == "number" then
      -- tod.time: 0 = noon, 0.5 = midnight
      local d = math.abs(tod.time - 0.5) * 2          -- 0 at midnight .. 1 at noon
      l = math.min(1, math.max(0, (d - 0.42) / 0.16)) -- fades around sunrise / sunset
    end
    local veh = be:getObjectByID(]] .. id .. [[)
    if veh then
      veh:queueLuaCommand("local c = controller.getController('gauges/customModules/dbgAmbient') if c and c.setLight then c.setLight(" .. l .. ") end")
    end
  ]]
  obj:queueGameEngineLua(cmd)
end

-- Highest boost the fitted turbo is set up for, read from the car's jbeam data (wastegate limit, PSI).
-- 0 when the car has no turbo or the value can't be found; the display then uses its fallback scale.
local maxBoost = nil

local function biggestNumber(x)
  if type(x) == "number" then return x end
  if type(x) == "string" then return tonumber(x) or 0 end
  local best = 0
  if type(x) == "table" then
    for _, val in pairs(x) do
      local n = biggestNumber(val)
      if n > best then best = n end
    end
  end
  return best
end

local function findMaxBoost()
  local best = 0
  local data = v and v.data
  if type(data) ~= "table" then return 0 end
  local names = {}
  for _, engineName in ipairs({"mainEngine", "engine"}) do
    local eng = data[engineName]
    if type(eng) == "table" and type(eng.turbocharger) == "string" then
      table.insert(names, eng.turbocharger)
    end
  end
  table.insert(names, "turbocharger")
  for _, name in ipairs(names) do
    local t = data[name]
    if type(t) == "table" then
      local limit = biggestNumber(t.wastegateLimit)
      if limit <= 0 then limit = biggestNumber(t.wastegateStart) end
      if limit > best then best = limit end
    end
  end
  return best
end

-- Automatic mounting. The "Auto" gauge parts carry the meshes for every mounting at once, named
-- dbgv<mounting><gauge>... (one letter per mounting). This looks at which interior meshes the car has,
-- works out the interior type and driving side, and hides the meshes of every mounting that doesn't match.
--   Ibishu Covet: A/D standard interior (LHD/RHD), B/E stripped interior, C/F roll cage
--   Ibishu 200BX: G/I A-pillar (the pillar is the same shape with every interior), H/J roll cage
local MOUNTINGS = {
  A = {"std", false},      B = {"stripped", false}, C = {"cage", false},
  D = {"std", true},       E = {"stripped", true},  F = {"cage", true},
  G = {"pillar", false},   H = {"cage", false},
  I = {"pillar", true},    J = {"cage", true},
}
local autoMeshes = nil      -- list of {name, visible}; false when the car has no auto-mounted gauge
local autoLabel = nil
local autoTimer = 99

local function mountingMatches(code, interior, rhd)
  local m = MOUNTINGS[code]
  if not m or m[2] ~= rhd then return false end
  if m[1] == interior then return true end
  -- "pillar" mountings sit on the A-pillar trim, which is the same with standard and stripped interiors
  return m[1] == "pillar" and interior ~= "cage"
end

local function detectMounting()
  local cage, stripped, rhd = false, false, false
  local found = {}
  local data = v and v.data
  if type(data) ~= "table" or type(data.flexbodies) ~= "table" then return nil, {} end
  for _, fb in pairs(data.flexbodies) do
    local mesh = type(fb) == "table" and fb.mesh
    if type(mesh) == "string" then
      if mesh:sub(1, 4) == "dbgv" and #mesh == 9 then
        table.insert(found, mesh)
      else
        local m = mesh:lower()
        -- a derby cage has no bar along the A-pillar, so the pillar mounting stays in use
        if m:find("rollcage", 1, true) and not m:find("derby", 1, true) then cage = true end
        if m:find("stripped_int", 1, true) then stripped = true end
        if m:find("dash", 1, true) and m:find("_rhd", 1, true) then rhd = true end
      end
    end
  end
  local interior = cage and "cage" or (stripped and "stripped" or "std")
  local list = {}
  for _, mesh in ipairs(found) do
    table.insert(list, {mesh, mountingMatches(mesh:sub(5, 5), interior, rhd)})
  end
  return interior .. (rhd and " RHD" or " LHD"), list
end

local function applyMounting()
  if autoMeshes == nil then
    local ok, label, list = pcall(detectMounting)
    if ok and label and #list > 0 then
      local shown = 0
      for _, m in ipairs(list) do if m[2] then shown = shown + 1 end end
      autoLabel, autoMeshes = label, list
      log("I", "pillar_pod_gauges", "automatic mounting: " .. label .. " (" .. shown .. " of " .. #list .. " meshes shown)")
    else
      autoMeshes = false
    end
  end
  if not autoMeshes then return end
  local cmd = {"local veh = be:getObjectByID(" .. obj:getID() .. ") if veh then"}
  for _, m in ipairs(autoMeshes) do
    table.insert(cmd, string.format(" veh:setMeshAlpha(%d, %q, false)", m[2] and 1 or 0, m[1]))
  end
  table.insert(cmd, " end")
  obj:queueGameEngineLua(table.concat(cmd))
end

local function updateGFX(dt)
  -- re-applied every second: the parts selector resets mesh visibility when it highlights parts
  autoTimer = autoTimer + dt
  if autoTimer > 1 and autoMeshes ~= false then
    autoTimer = 0
    pcall(applyMounting)
  end
end

-- Exhaust gas temperature (deg C) from the engine's thermal simulation. nil when the car has no
-- combustion engine or its thermals aren't running; the display then shows zero.
local egtEngine = nil       -- false when there is no engine to read

local function readEgt()
  if egtEngine == nil then
    egtEngine = false
    local ok, list = pcall(function() return powertrain.getDevicesByType("combustionEngine") end)
    if ok and type(list) == "table" then
      for _, dev in pairs(list) do
        if type(dev) == "table" and type(dev.thermals) == "table" then egtEngine = dev break end
      end
    end
  end
  if not egtEngine then return nil end
  local t = egtEngine.thermals and egtEngine.thermals.exhaustTemperature
  return type(t) == "number" and t or nil
end

-- Data for the multi-function display: tyre pressure and temperature, brake temperature, g-force,
-- fuel range and outside temperature. Wheel names are the car's own (FL, FR, RL, RR on most cars).
local mfd = {tp = {}, tt = {}, bt = {}, ws = {}}
local trip = {dist = 0, fuelUsed = 0, lastFuel = nil}

local function readMfd(dt)
  local tp, tt, bt, ws = {}, {}, {}, {}
  local envP = obj:getEnvPressure()
  for _, wd in pairs(wheels.wheels or {}) do
    local name = wd.name
    if name then
      local group = wd.pressureGroup and v.data.pressureGroups and v.data.pressureGroups[wd.pressureGroup]
      if group then tp[name] = math.max((obj:getGroupPressure(group) - envP) * 0.001, 0) end   -- kPa above outside air
      if wd.wheelID then
        local k = obj:getWheelAvgTemperature(wd.wheelID)
        if type(k) == "number" and k > 0 then tt[name] = k - 273.15 end
      end
      if type(wd.brakeSurfaceTemperature) == "number" then bt[name] = wd.brakeSurfaceTemperature end
      if type(wd.wheelSpeed) == "number" then ws[name] = wd.wheelSpeed end                          -- m/s
    end
  end
  mfd.tp, mfd.tt, mfd.bt, mfd.ws = tp, tt, bt, ws
  mfd.glat = (sensors.gx2 or sensors.gx or 0) / 9.81
  mfd.glon = (sensors.gy2 or sensors.gy or 0) / 9.81
  mfd.envT = obj:getEnvTemperature() - 273.15
  -- range from the average consumption since spawn (needs half a kilometre of driving first)
  local e = electrics.values
  trip.dist = trip.dist + math.abs(e.wheelspeed or 0) * dt
  local fuel = e.fuelVolume
  if type(fuel) == "number" then
    if trip.lastFuel and fuel < trip.lastFuel and trip.lastFuel - fuel < 1 then trip.fuelUsed = trip.fuelUsed + (trip.lastFuel - fuel) end
    trip.lastFuel = fuel
    if trip.dist > 500 and trip.fuelUsed > 0.01 then
      mfd.range = fuel / (trip.fuelUsed / (trip.dist / 1000))               -- km
    else
      mfd.range = 0
    end
  end
end

local function updateGaugeData(moduleData, dt)
  timer = timer + (dt or 0)
  if timer > 2 then
    timer = 0
    pcall(requestLight)
  end
  moduleData.light = light
  if maxBoost == nil then
    local ok, res = pcall(findMaxBoost)
    maxBoost = (ok and tonumber(res)) or 0
  end
  moduleData.maxBoost = maxBoost
  local okE, egt = pcall(readEgt)
  moduleData.egt = (okE and egt) or 0
  pcall(readMfd, dt or 0)
  moduleData.mfd = mfd
end

local function setupGaugeData(properties)
end

local function reset()
  timer = 99
  maxBoost = nil
  autoMeshes = nil
  autoTimer = 99
  egtEngine = nil
  trip = {dist = 0, fuelUsed = 0, lastFuel = nil}
end

local function init(jbeamData)
end

M.init = init
M.reset = reset
M.updateGFX = updateGFX
M.setupGaugeData = setupGaugeData
M.updateGaugeData = updateGaugeData
M.setLight = setLight

return M
