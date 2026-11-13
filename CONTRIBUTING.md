# Contributing

Thanks for wanting to help with Pillar Pod Digital Gauges. Bug reports, testing on other setups, fixes and new car support are all welcome.

## Reporting a bug

Open an [issue](https://github.com/likeBloodMoon/Pillar-Pod-Digital-Gauges/issues) and include:

- the mod version (from the release zip name) and your BeamNG.drive version
- the car and configuration, and which parts you fitted (pillar gauges, display, cluster)
- left- or right-hand drive, and your unit settings if a reading looks wrong
- a screenshot from the driver's seat
- your `beamng.log` if something doesn't load or a screen stays blank (it's in `%LocalAppData%\BeamNG\BeamNG.drive\current`)

Security problems go through private reporting instead. See [SECURITY.md](SECURITY.md).

## Suggesting a feature

Open an issue first and describe what you'd like to see and on which car. A screenshot or a photo of a real gauge helps a lot. Talking it through before you build saves work on both sides.

## Making changes

### How the repo is laid out

| Path | What it is |
|---|---|
| `vehicles/common/pillar_pod_gauges/` | Meshes (`.dae`), materials, textures, fonts and the screen pages: `screen.html` (round gauges), `mfd.html` (pillar display), `cluster.html` (digital cluster) |
| `vehicles/covet/`, `vehicles/bx/` | The parts for each car. **Generated, don't edit by hand** |
| `lua/vehicle/controller/gauges/customModules/` | Automatic mounting, ambient light, wastegate limit, EGT and the display data |
| `tools/` | Scripts that generate the parts and meshes, and the validator |

### Parts (`.jbeam`) are generated

The part files are written by `tools/gen_jbeam.py`. To change a part, change the generator and regenerate:

    python tools/gen_jbeam.py --car covet vehicles/covet/covet_pillar_pod_gauges.jbeam
    python tools/gen_jbeam.py --car bx vehicles/bx/bx_pillar_pod_gauges.jbeam

The validator checks that the committed files match the generator, so a hand edit fails CI.

### Screens

The screens are plain HTML canvas pages. You can open them in a desktop browser and drive them from the developer console:

    setup({ uiUnitPressure: "bar", uiUnitTemperature: "c" })
    updateData({ electrics: { rpm: 5000, wheelspeed: 30, gear: 3, ignitionLevel: 2, fuel: 0.5, fuelVolume: 20, watertemp: 90, turboBoost: 12 }, customModules: {} })

Keep in mind how they behave inside the game:

- **Draw from `updateData`.** The game calls it every frame, and page timers can be paused inside the game, so a screen that only animates on a timer will freeze.
- **Size text for the driver's seat.** In the game the screens are small, so check readability at about a third of full size.
- **Keep everything inside the page.** No external fonts, scripts or network requests. Bundled files only.

### Meshes

The mesh scripts in `tools/` need geometry from your own copy of the game (extracted with `tools/extract_cabin.py`). **Never commit the game's meshes or anything extracted from them.** `*.npy` is in `.gitignore` for that reason. Only the mod's own meshes go in the repo.

### Before you open a pull request

1. Run the validator. It needs Python 3 and, for the JavaScript checks, Node.js:

       python tools/validate_assets.py

2. Test in the game: load the car, fit the parts, sit in the driver's seat and check the screens update.
3. Keep each pull request to one change and explain what it does and how you tested it. Screenshots from the game help for anything visual.

CI runs the validator on every push and pull request.

## Releases

Releases are made by the maintainer. Pushing a `v*` tag on `main` builds `pillar_pod_gauges_<tag>.zip` and attaches it to a GitHub release. Always tag **after** the last pull request is merged into `main`.

## Licence

By contributing you agree that your contribution is released under the project's [MIT licence](LICENSE). Don't add content you don't have the rights to, such as BeamNG's own files, other mods' assets or fonts without an open licence.
