-- This Source Code Form is subject to the terms of the MIT licence (see LICENSE).
-- Data module for the digital cluster: its own instance of dbgAmbient (ambient light, wastegate limit,
-- exhaust temperature and the display data), so the cluster works without the pillar gauges and the
-- two never load the same controller twice.

local M = rerequire("controller/gauges/customModules/dbgAmbient")
M.type = "auxiliary"
return M
