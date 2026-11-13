# Pillar Pod Digital Gauges

Digital boost and oil temperature gauges on A-pillar and roll-cage pods for BeamNG.drive.
Currently for the Ibishu Covet and the Ibishu 200BX.

## Install

Download the mod zip (named after the version, for example `pillar_pod_gauges_v1.1.0.zip`) from the
[latest release](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/releases/latest) and
put it in your BeamNG `mods` folder. Do not unpack it. When updating, remove the older version's
zip first so the game does not load two copies.

GitHub's own "Download ZIP" of the source will not work as a mod, because it wraps everything in
an extra folder. To build the mod zip yourself, zip the `vehicles` and `lua` folders together so
that both sit at the top level.

## Use

Parts selector → **Additional Modification** → **Digital Pillar Gauges**.

There are two positions, **Lower Gauge** and **Upper Gauge**. Each can hold any of the gauge
types: boost, oil temperature, coolant temperature or fuel level. By default the lower one is boost
and the upper one is empty.

Every gauge type comes with **Automatic Mounting** in black or silver (silver bezel, white face).
It looks at the car's interior and puts the gauge in the right place: on the A-pillar trim, on the
bare pillar of a stripped / race / rally interior, or on the roll cage bar, for left- or right-hand
drive. Boost (lower) and oil temperature (upper) are also offered in fixed mountings, one per
interior type, if you want to choose yourself.

On the 200BX the A-pillar has the same shape with every interior, coupe or liftback, so there is
one pillar mounting plus the roll cage one. With the derby cage, which has no bar along the
A-pillar, the gauges stay on the pillar.

## Features

- Live display with a 24-LED sweep: vacuum in blue, boost in green, red overboost zone
- LED scale and overboost warning set themselves from the turbo's wastegate limit
- Peak recall after each pull, start-up sweep, reads zero with the engine stopped
- Shift light: the whole LED ring flashes red near the rev limit
- Coolant temperature and fuel level gauges, alongside boost and oil temperature
- Blue COLD mark on the temperature gauges until the engine is warm; low-fuel warning on the fuel gauge
- PSI / bar / kPa and °C / °F follow the game's unit settings
- Dims automatically at night and with the headlights on
- Tuning menu sliders (category **Gauges**): overboost warning, peak recall time, shift light
  on/off, night brightness, oil and coolant warning and cold-mark temperatures, low-fuel warning

## Known limits

- It uses each car's single "Additional Modification" slot, so it cannot be combined with another
  mod that uses that slot.
- The right-hand-drive mountings are mirrored from the left-hand ones. On the 200BX they were
  checked against the right-hand dashboards' meshes, but not yet in game.
- Each mounting has its own pod mesh shaped to that interior, so moving a gauge by editing
  coordinates only works for small nudges.

## Layout

- `vehicles/common/pillar_pod_gauges/` — meshes, materials, face textures and the display page
- `vehicles/covet/`, `vehicles/bx/` — the parts for each car
- `lua/vehicle/controller/gauges/customModules/` — ambient light, wastegate limit and automatic
  mounting
- `tools/` — the scripts the generated files came from

## Licence

MIT, see [LICENSE](LICENSE). The licence covers this mod's own files. BeamNG.drive and its
vehicles belong to BeamNG GmbH and are not part of this repository.
