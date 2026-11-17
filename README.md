# Pillar Pod Digital Gauges

[![Latest release](https://img.shields.io/github/v/release/likeBloodMoon/Pillar-Pod-Digital-Gauges?label=release)](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/likeBloodMoon/Pillar-Pod-Digital-Gauges/total?label=downloads)](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/releases)
[![Validate mod assets](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/actions/workflows/validate-assets.yml/badge.svg?branch=main)](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/actions/workflows/validate-assets.yml)
[![BeamNG repository](https://img.shields.io/badge/BeamNG-repository-orange)](https://www.beamng.com/resources/pillar-pod-digital-gauges.40320/)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-blue)](LICENSE)
[![Support on Ko-fi](https://img.shields.io/badge/Ko--fi-support-ff5e5b?logo=ko-fi&logoColor=white)](https://ko-fi.com/likebloodmoon)

Digital gauges for BeamNG.drive. Round gauges on the A-pillar or roll cage, a pillar-mounted
multi-function display, and a full digital instrument cluster that replaces the car's own gauges.

Works on the **Ibishu Covet** and the **Ibishu 200BX**. The display and the cluster are Covet only
for now.

**Version 1.2.1** · [Changelog](CHANGELOG.md)

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

![Boost and oil temperature gauges: start-up sweep, a pull to full boost, peak recall, shut-down sweep](docs/demo-sweep.gif)

*Ignition on, a pull to full boost, lift off (the boost gauge shows the peak), ignition off.*

Parts selector → **Additional Modification** → **Digital Pillar Gauges**, then pick what goes in
the **Lower Gauge** and **Upper Gauge** positions. Each position can hold any gauge:

| Gauge | Shows |
|---|---|
| Boost | Vacuum and boost on a 24-LED sweep, scaled to the turbo's wastegate limit, with peak recall |
| Oil temperature | Oil temperature with a blue COLD mark until the engine is warm |
| Coolant temperature | Coolant temperature with a COLD mark and a warning limit |
| Exhaust gas temperature | EGT from the game's engine heat simulation; in °F a full 4-digit readout (1370) |
| Fuel level | Fuel left, with a low-fuel warning |
| Tachometer | Engine speed in thousands (6.8 = 6800 rpm), scaled to the engine's rev limit, with a shift light |

Under the label, a blue **PEAK** light comes on for a moment whenever the reading sets a new high
for the drive (in the top part of the scale), and a red **WARN** light stays on while it's past the
warning limit: overboost, overheating, low fuel, or the shift point on the tachometer. The fuel gauge
has only WARN.

If the car doesn't have the reading at all, for example the boost gauge on a car without a turbo or
supercharger, the gauge shows `---` with the LED ring dark instead of a made-up 0. The display and the
cluster do the same.

Every gauge comes as **Automatic Mounting**, in black or in silver with a white face. It finds its
own place: on the A-pillar trim, on the bare pillar of a stripped or race interior, or on the roll
cage bar, for left- or right-hand drive.

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
- **Right:** one page at a time: Boost, Tyres, Engine (oil and EGT), Brakes, G-Force, Trip
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

- Colour of the round gauges' LED ring and digits: 0 green with red digits (default), 1 white,
  2 amber, 3 blue, 4 purple, 5 super green. Purple and super green also light the labels and a
  glowing rim round the face. Warnings stay red in every colour
- Overboost warning, peak recall time, shift light on/off
- Tachometer: shift light on/off, the RPM where it starts, scale maximum
- Oil, coolant and exhaust warning temperatures, cold-mark temperatures, low-fuel warning
- Night brightness: one setting for all the round gauges, and separate ones for the display and the
  cluster
- First page shown on the display and on the cluster
- Shut-down sweep: when the ignition is switched off, the round gauges sweep their LED ring and fade
  out and the screens fade to black (1 = on, 0 = switch off at once)

## Known limits

- The pillar gauges and the display use the car's single **Additional Modification** slot, so they
  can't be combined with another mod that uses that slot. The cluster uses the Gauges slot instead.

## Roadmap

Planned work is tracked as [milestones](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/milestones), one per release:

- [1.3](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/milestone/1): peak and warning lights on every gauge, `---` when a car
  doesn't report a reading, tachometer and G-meter gauges, key bindings to show and reset the peak,
  a shorter parts list with only automatic mounting, and new styles: colour themes, a full purple
  version, needle faces, a smoked-lens finish and light and dark screens for the display and cluster
- [1.4](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/milestone/2): the Pessima, Sunburst and ETK 800, the display and cluster on the 200BX,
  a triple pillar pod and other mounts
- [1.5](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/milestone/3): a race-dash cluster with a shift-light strip, a warning banner and timers,
  and a replay of the last 3 minutes on the display
- [2.0](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/milestone/4): estimated readings such as oil pressure and air-fuel ratio (labelled as
  estimates on the gauge) and ready-made configs

The plan can change. Give an issue a 👍 if you want it, or post an idea in
[Discussions](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/discussions). If you'd like to help, the issues labelled
[good first issue](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/labels/good%20first%20issue) are the easiest to start with; see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Support

The mod is free and stays free. If it made your drives better and you'd like to say thanks, you can
[buy me a coffee on Ko-fi](https://ko-fi.com/likebloodmoon). It helps me spend more evenings on new
gauges, more cars and fixes. Bug reports, ideas and screenshots of your build in
[Discussions](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/discussions) help just as
much.

## For developers

- `vehicles/common/pillar_pod_gauges/`: meshes, materials, textures, fonts and the screen pages
  (`screen.html`, `mfd.html`, `cluster.html`)
- `vehicles/covet/`, `vehicles/bx/`: the parts for each car (generated by `tools/gen_jbeam.py`)
- `lua/vehicle/controller/gauges/customModules/`: automatic mounting, ambient light, wastegate
  limit, EGT and the display's data
- `tools/`: the scripts that generate the meshes and parts, and `validate_assets.py`, which CI runs
  on every pull request

To build the mod zip yourself, zip the `vehicles` and `lua` folders so both sit at the top level of
the zip. Pushing a `v*` tag builds the zip and attaches it to a GitHub release.

## Licence

MIT, see [LICENSE](LICENSE). The licence covers this mod's own files. BeamNG.drive and its vehicles
belong to BeamNG GmbH and are not part of this repository.

The screens use the Barlow Semi Condensed typeface by the Barlow Project Authors, under the SIL Open
Font License 1.1 (`vehicles/common/pillar_pod_gauges/fonts/OFL.txt`).
