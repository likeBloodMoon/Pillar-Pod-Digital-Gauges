# Changelog

## 1.2.1

Fixes and polish. No new gauges, cars or parts.

### Fixed
- **200BX: pillar gauges were too big and too close.** They were placed for an estimated driver
  camera that was about 15 cm too far back. Refitted to the camera measured in game: both the trim
  and roll-cage mountings moved about 10 cm down the pillar, and from the driver's seat the gauges
  now look the same size as on the Covet. They're fully in view and out of the upper windscreen.
- **EGT gauge in °F** shows the full value with four digits (1370) instead of hundreds (13.7). The
  start-up test shows 8888. In °C it keeps three digits.

### Added
- **Shut-down sweep.** When the ignition is switched off, the round gauges sweep their LED ring up
  and back down while the digits fade out (1 s). The display and the cluster fade to black (0.8 s).
  It doesn't run when the car spawns, after a reset, or when the engine stalls with the ignition
  still on. Turn it off in Tuning → Gauges → **Shut-Down Sweep**.

### Changed
- **Easier to read from the driver's seat.** The round gauges have bigger digits (about 20 %), and
  the label (BOOST, OIL TEMP ...) and unit are almost twice as large. From the seat the whole face is
  only about 100 pixels across, and the old 4-pixel labels couldn't be read. PEAK and COLD use the
  same large text in place of the label.

### Checked
- **Right-hand drive.** Every RHD mounting (pillar gauges, display, cluster) was checked against the
  game's own RHD interiors on both cars instead of a mirror of the LHD side. All of them fit, so
  nothing needed moving.

## 1.2.0

- **Digital instrument cluster** for the Covet (standard dashboard and race dashboard): bar tach,
  speed, gear, fuel, coolant and six pages (Boost, Tyres, Engine, Brakes, G-Force, Trip).
- **Multi-function display** for the Covet's A-pillar: boost, tyres, engine, brakes and g-force
  pages.
- **New gauges:** coolant temperature, fuel level and exhaust gas temperature; any gauge can go in
  either position.
- **Ibishu 200BX** support with automatic mounting.

## 1.1.0

- Boost and oil temperature gauges on A-pillar pods for the Ibishu Covet.
- Automatic mounting for every Covet interior (pillar trim, bare pillar of stripped / race / rally
  interiors, roll cage), left- and right-hand drive, in black or silver.
- Shift light on the boost gauge and a cold mark on the oil temperature gauge.
