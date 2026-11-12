# Pillar Pod Digital Gauges

Digital boost and oil temperature gauges on A-pillar and roll-cage pods for BeamNG.drive.
Currently for the Ibishu Covet.

## Install

Zip the `vehicles` and `lua` folders together so that both sit at the top level of the zip, name
it `pillar_pod_gauges.zip`, and put it in your BeamNG `mods` folder. Do not unpack it.

GitHub's own "Download ZIP" will not work as it is, because it wraps everything in an extra folder.

## Use

Parts selector → **Additional Modification** → **Digital Pillar Gauges**.

**Boost Gauge** and **Oil Temp Gauge** each list one entry per interior type:

- A-Pillar, Standard Interior
- A-Pillar, Stripped / Race / Rally Interior
- Roll Cage Bar

Each comes in left- and right-hand drive, and in black or silver (silver bezel, white face).
Fit one gauge or both; boost sits in the lower position and oil temperature above it.

**Additional Modification (other mods)** is a pass-through slot: it accepts any part made for the
Covet's Additional Modification slot, so another mod can be fitted alongside the gauges.

## Features

- Live display with a 24-LED sweep: vacuum in blue, boost in green, red overboost zone
- LED scale and overboost warning set themselves from the turbo's wastegate limit
- Peak recall after each pull, start-up sweep, reads zero with the engine stopped
- PSI / bar / kPa and °C / °F follow the game's unit settings
- Dims automatically at night and with the headlights on
- Tuning menu sliders (category **Gauges**): overboost warning, peak recall time, night
  brightness, oil temperature warning

## Known limits

- It sits in the Covet's single "Additional Modification" slot. To use another mod that needs that
  slot at the same time, fit that mod's part in **Additional Modification (other mods)** inside
  Digital Pillar Gauges. That gives room for one other mod.
- The right-hand-drive mountings are mirrored from the left-hand ones and have not been checked
  against the right-hand interior.
- Each mounting has its own pod mesh shaped to that interior, so moving a gauge by editing
  coordinates only works for small nudges.

## Layout

- `vehicles/common/pillar_pod_gauges/` — meshes, materials, face textures and the display page
- `vehicles/covet/` — the Covet parts
- `lua/vehicle/controller/gauges/customModules/` — ambient light and wastegate-limit module
- `tools/` — the scripts the generated files came from
