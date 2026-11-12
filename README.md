# Pillar Pod Digital Gauges

Digital boost and oil temperature gauges on A-pillar and roll-cage pods for BeamNG.drive.
Currently for the Ibishu Covet.

## Install

Download `pillar_pod_gauges.zip` from the
[latest release](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/releases/latest) and
put it in your BeamNG `mods` folder. Do not unpack it.

GitHub's own "Download ZIP" of the source will not work as a mod, because it wraps everything in
an extra folder. To build the mod zip yourself, zip the `vehicles` and `lua` folders together so
that both sit at the top level.

## Use

Parts selector → **Additional Modification** → **Digital Pillar Gauges**.

**Boost Gauge** and **Oil Temp Gauge** each offer **Automatic Mounting** in black or silver
(silver bezel, white face). It looks at the car's interior and puts the gauge in the right place:
on the A-pillar trim, on the bare pillar of a stripped / race / rally interior, or on the roll
cage bar, for left- or right-hand drive.

The fixed mountings are still listed below it, one per interior type, if you want to choose
yourself. Fit one gauge or both; boost sits in the lower position and oil temperature above it.

## Features

- Live display with a 24-LED sweep: vacuum in blue, boost in green, red overboost zone
- LED scale and overboost warning set themselves from the turbo's wastegate limit
- Peak recall after each pull, start-up sweep, reads zero with the engine stopped
- Shift light: the whole LED ring flashes red near the rev limit
- Blue COLD mark on the oil gauge until the oil is up to temperature
- PSI / bar / kPa and °C / °F follow the game's unit settings
- Dims automatically at night and with the headlights on
- Tuning menu sliders (category **Gauges**): overboost warning, peak recall time, shift light
  on/off, night brightness, oil temperature warning, cold-mark temperature

## Known limits

- It uses the Covet's single "Additional Modification" slot, so it cannot be combined with another
  mod that uses that slot.
- The right-hand-drive mountings are mirrored from the left-hand ones and have not been checked
  against the right-hand interior.
- Each mounting has its own pod mesh shaped to that interior, so moving a gauge by editing
  coordinates only works for small nudges.

## Layout

- `vehicles/common/pillar_pod_gauges/` — meshes, materials, face textures and the display page
- `vehicles/covet/` — the Covet parts
- `lua/vehicle/controller/gauges/customModules/` — ambient light, wastegate limit and automatic
  mounting
- `tools/` — the scripts the generated files came from

## Licence

MIT, see [LICENSE](LICENSE). The licence covers this mod's own files. BeamNG.drive and its
vehicles belong to BeamNG GmbH and are not part of this repository.
