-- Ambient light (automatic display dimming) and turbo wastegate limit (automatic LED scale) for the
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

local function updateGFX(dt)
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
end

local function setupGaugeData(properties)
end

local function reset()
  timer = 99
  maxBoost = nil
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
