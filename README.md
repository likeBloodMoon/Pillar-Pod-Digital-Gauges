# Pillar Pod Digital Gauges

Digital gauges for BeamNG.drive. Round gauges on the A-pillar or roll cage, a pillar-mounted
multi-function display, and a full digital instrument cluster that replaces the car's own gauges.

Works on the **Ibishu Covet** and the **Ibishu 200BX**. The display and the cluster are Covet only
for now.

![Digital cluster on the Covet's race dashboard](docs/cluster-race-dash.jpg)

## Install

1. Download `pillar_pod_gauges_<version>.zip` from the
   [latest release](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/releases/latest).
2. Put it in your BeamNG `mods` folder as it is. Do not unpack it.
3. When updating, delete the older version's zip first so the game doesn't load two copies.

GitHub's green "Download ZIP" button gives you the source code, not the mod, and won't load in the
game. Use the zip from the release.

## What's in it

### Pillar gauges (Covet and 200BX)

Parts selector → **Additional Modification** → **Digital Pillar Gauges**, then pick what goes in
the **Lower Gauge** and **Upper Gauge** positions. Each position can hold any gauge:

| Gauge | Shows |
|---|---|
| Boost | Vacuum and boost on a 24-LED sweep, scaled to the turbo's wastegate limit, with peak recall |
| Oil temperature | Oil temperature with a blue COLD mark until the engine is warm |
| Coolant temperature | Coolant temperature with a COLD mark and a warning limit |
| Exhaust gas temperature | EGT from the game's engine heat simulation |
| Fuel level | Fuel left, with a low-fuel warning |

Choose **Automatic Mounting** (black, or silver with a white face) and the gauge finds its own
place: on the A-pillar trim, on the bare pillar of a stripped or race interior, or on the roll cage
bar, for left- or right-hand drive. Fixed mountings for each interior are there too if you want to
pick yourself.

### Digital cluster (Covet)

![Digital cluster on the Covet's standard dashboard](docs/cluster-standard-dash.jpg)

Parts selector → **Gauges** → **Pillar Pod Digital Cluster**. It replaces the Covet's instrument
cluster with a wide screen. On the standard dashboard the screen fills the old gauge opening; with
the race dashboard choose **Pillar Pod Digital Cluster (Race Dash)** and a screen unit sits on the
carbon panel. It uses the car's own Gauges slot, so it works alongside the pillar gauges.

- **Top:** bar tachometer that turns amber near the limit, red past it, and flashes at the shift point
- **Middle:** speed and gear, with warning lights only when they're on (parking brake, check
  engine, overheating, headlights)
- **Left:** fuel and coolant temperature with bars
- **Right:** one page at a time — Boost, Tyres, Engine (oil and EGT), Brakes, G-Force, Trip
  (range, outside temperature, drive time)

The layout is built to be read from the driver's seat: few readings, large numbers, and everything
inside the part of the screen the steering wheel doesn't cover.

### Multi-function display (Covet)

**Lower Gauge** → **Multi-Function Display** puts a portrait colour screen on the A-pillar instead
of a round gauge (leave the Upper Gauge empty). It mounts itself on the standard interior, the
stripped interior or the roll cage, left- or right-hand drive.

- **Boost:** dial scaled to the wastegate limit, with the session maximum
- **Tyres:** pressure, tread temperature and wheel speed per wheel; low pressure turns amber, a flat red
- **Engine:** oil, coolant and exhaust gas temperature and engine speed, with warning limits
- **Brakes:** temperature per brake
- **G-Force:** friction circle with a trace and peak lateral and longitudinal g

Status rows along the top and bottom show warning lights, fuel, range, drive time, gear, outside
and coolant temperature.

### Changing pages

Click the button under the display, or the page panel on the cluster, in the cabin. You can also
bind **Display: next page** in Options → Controls. The display and the cluster flip together.

## Settings

Everything follows the game's unit settings (psi / bar / kPa, °C / °F, km/h / mph, litres /
gallons). All screens dim at night and with the headlights on.

Tuning menu, category **Gauges**:

- Overboost warning, peak recall time, shift light on/off
- Oil, coolant and exhaust warning temperatures, cold-mark temperatures, low-fuel warning
- Night brightness for the gauges, the display and the cluster
- First page shown on the display and on the cluster

## Known limits

- The pillar gauges and the display use the car's single **Additional Modification** slot, so they
  can't be combined with another mod that uses that slot. The cluster uses the Gauges slot instead.
- On the 200BX the pillar gauges can sit too large and close to the driver's camera. A fix is
  planned.
- Right-hand-drive mountings are mirrored from the left-hand ones and haven't all been checked in
  game.
- In °F the round EGT gauge reads in hundreds (13.7 = 1370 °F), because its display has three digits.
- Each mounting has a pod mesh shaped to that interior, so moving a gauge by editing coordinates
  only works for small nudges.

## For developers

- `vehicles/common/pillar_pod_gauges/` — meshes, materials, textures, fonts and the screen pages
  (`screen.html`, `mfd.html`, `cluster.html`)
- `vehicles/covet/`, `vehicles/bx/` — the parts for each car (generated by `tools/gen_jbeam.py`)
- `lua/vehicle/controller/gauges/customModules/` — automatic mounting, ambient light, wastegate
  limit, EGT and the display's data
- `tools/` — the scripts that generate the meshes and parts, and `validate_assets.py`, which CI runs
  on every pull request

To build the mod zip yourself, zip the `vehicles` and `lua` folders so both sit at the top level of
the zip. Pushing a `v*` tag builds the zip and attaches it to a GitHub release.

## Licence

MIT, see [LICENSE](LICENSE). The licence covers this mod's own files. BeamNG.drive and its vehicles
belong to BeamNG GmbH and are not part of this repository.

The screens use the Barlow Semi Condensed typeface by the Barlow Project Authors, under the SIL Open
Font License 1.1 (`vehicles/common/pillar_pod_gauges/fonts/OFL.txt`).
