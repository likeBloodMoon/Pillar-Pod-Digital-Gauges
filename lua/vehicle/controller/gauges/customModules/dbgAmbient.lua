-- Ambient light (automatic display dimming), turbo wastegate limit (automatic LED scale) and
-- automatic mounting for the digital pillar gauges.
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
-- dbgv<mounting><gauge>... (mounting A-F). This looks at which interior meshes the car has, picks the
-- matching mounting and hides the meshes of all the others.
--   A/D standard interior (LHD/RHD), B/E stripped interior, C/F roll cage
local autoMeshes = nil      -- list of {name, code}; false when the car has no auto-mounted gauge
local autoCode = nil
local autoTimer = 99

local function detectMounting()
  local cage, stripped, rhd = false, false, false
  local list = {}
  local data = v and v.data
  if type(data) ~= "table" or type(data.flexbodies) ~= "table" then return nil, list end
  for _, fb in pairs(data.flexbodies) do
    local mesh = type(fb) == "table" and fb.mesh
    if type(mesh) == "string" then
      if mesh:sub(1, 4) == "dbgv" and #mesh == 9 then
        table.insert(list, {mesh, mesh:sub(5, 5)})
      else
        local m = mesh:lower()
        if m:find("rollcage", 1, true) then cage = true end
        if m:find("stripped_int", 1, true) then stripped = true end
        if m:find("dash", 1, true) and m:find("_rhd", 1, true) then rhd = true end
      end
    end
  end
  local code
  if cage then code = rhd and "F" or "C"
  elseif stripped then code = rhd and "E" or "B"
  else code = rhd and "D" or "A" end
  return code, list
end

local function applyMounting()
  if autoMeshes == nil then
    local ok, code, list = pcall(detectMounting)
    if ok and code and #list > 0 then
      autoCode, autoMeshes = code, list
      log("I", "pillar_pod_gauges", "automatic mounting: " .. code .. " (" .. #list .. " meshes managed)")
    else
      autoMeshes = false
    end
  end
  if not autoMeshes then return end
  local cmd = {"local veh = be:getObjectByID(" .. obj:getID() .. ") if veh then"}
  for _, m in ipairs(autoMeshes) do
    table.insert(cmd, string.format(" veh:setMeshAlpha(%d, %q, false)", m[2] == autoCode and 1 or 0, m[1]))
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
  autoMeshes = nil
  autoTimer = 99
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
