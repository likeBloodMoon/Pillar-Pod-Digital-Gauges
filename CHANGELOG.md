# Changelog

## Unreleased

### Added
- **Event recorder and Event History app.** The car records moments worth a second look: overboost,
  the rev limiter, coolant or oil overheating, hard braking, a new lateral-g high, impacts, stalls
  and engine damage the game reports. Each event keeps a few seconds of readings before and after
  it and a summary at its peak, all from the game's own data. The new **Pillar Pod Event History**
  UI app lists them with plots and a timeline of the drive. Drives are saved to
  `pillar_pod_gauges/recordings` in the BeamNG user folder and open in `viewer/index.html` on a PC,
  which can also export any event as CSV.
- **Tachometer** for the pillar gauges, in either position. The LED ring runs up to the engine's rev
  limit, with the last three (red) LEDs past it, and the digits show thousands (6.8 = 6800 rpm). The
  whole ring flashes red at the shift point. Tuning → Gauges has the shift light on/off, the RPM it
  starts at (96 % of the limit by default) and an optional fixed scale maximum.
- **PEAK and WARN lights** on every round gauge, under the label. PEAK (blue) lights for 1.5 s
  whenever the reading sets a new high for the drive in the top 40 % of the scale, so a warming
  engine or cruising doesn't keep it on. WARN (red) stays on while the reading is past the warning
  limit (overboost, oil, coolant or exhaust too hot, low fuel), and on the tachometer from the shift
  point. Both light up with the start-up test. The fuel gauge has WARN only. The unlit lights are
  printed on the faces, which were re-baked.
- **`---` for a reading the car doesn't have.** The game sends 0 for a value a car doesn't
  simulate, so a boost gauge on a car without a turbo read 0.0 and looked broken. The mod's module
  now tells the screens which readings are really missing (boost, oil and coolant temperature,
  fuel, engine speed, exhaust temperature). The round gauges show dashes with the ring dark and no
  PEAK or WARN; the display and the cluster show `---` with an empty bar. A real 0 still reads 0.

### Changed
- **One Night Brightness setting for all round gauges** (Tuning → Gauges → Gauges: Night
  Brightness) instead of one per gauge type. Two fitted gauges now dim the same, and swapping a
  gauge for another type keeps the setting. The display and the cluster keep their own, since those
  screens are much brighter. A config saved with the old per-gauge values goes back to the default
  (12 %) once; set it again and save.
- **Only automatic mounting.** The fixed mountings (one part per interior, side and finish for the
  Boost and Oil Temp gauges) are gone, since automatic mounting finds the same spots by itself. The
  parts list is much shorter (30 parts instead of 54 on the Covet, 25 instead of 41 on the 200BX),
  and the mod's mesh file is about a fifth smaller.
  **If you saved a config with a fixed mounting**, that gauge is missing when you load it: pick the
  gauge again with Automatic Mounting and save the config.

### Fixed
- **Screens flashed while the time of day changed.** The mod asked the game for the light level every
  2 seconds and the screens jumped straight to each new value, so dragging the time-of-day slider made
  them blink between bright and dim. The mod now asks twice a second and the screens fade to the new
  brightness over about a second. The headlights still dim them at once.
- **The display's range read double** with the display and an Upper Gauge fitted. Every screen asked the mod's module for its data, and the module did all its reading
  on each call, so the trip distance was added once per screen. The module now reads everything once
  per frame and each screen only copies the latest values. Tyre, brake and g-force readings are only
  taken when the display or the cluster is fitted.

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
