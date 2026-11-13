# Build tools

These scripts produce or validate the mod's generated assets.

| Script | What it does |
|---|---|
| `find_positions.py` | Casts rays from the driver's eye into the car's interior meshes to find a gauge position that is fully visible for each mounting |
| `extract_cabin.py` | Pulls named interior meshes out of the game's car Collada file for the two scripts below |
| `find_positions_bx.py` | `find_positions.py` set up for the 200BX |
| `find_mfd_position.py` | Finds the multi-function display's position on the Covet's A-pillar |
| `build_mfd_mesh.py` | Builds the display housing, page button and the pod onto the pillar |
| `build_cluster_mesh.py` | Builds the digital cluster screens: the gauge-face screen and the race-dash screen unit |
| `build_pod_mesh.py` | Builds one gauge + pod mesh (Blender `bpy`), ray-casting each of the pod's 40 columns onto the interior surface |
| `export_dae.py` | Writes all pod, bezel and screen meshes into the Collada file |
| `gen_jbeam.py` | Generates a car's part file (all mountings, finishes, sliders): `gen_jbeam.py --car covet\|bx <out>` |
| `fit_check_render.py` | Software render of the car interior with the gauges, used to check the fit |
| `build_release.py` | Assembles the release folder and zip from the working files |
| `bake_faces.py` | Runs `bake_faceplates.html` in headless Chrome and writes all six face textures |
| `bake_faceplates.html` | Bakes the printed face textures from the display page's own drawing code |
| `validate_assets.py` | Checks JBeam structure, DAE mesh/material references, material texture paths, JavaScript syntax, Python syntax, and generated JBeam consistency |

## Run validation locally

Requirements: Python 3.10+ and Node.js 18+.

From the repository root:

```bash
python tools/validate_assets.py
```

The validator uses only Python's standard library and Node's built-in syntax checker. It does not launch BeamNG or Blender, so it cannot verify in-game fit, rendering, or game-side JBeam semantics.

The placement and pod-shaping steps need the car's interior meshes extracted from the game's own `covet.dae` / `bx.dae`. Those are BeamNG's files and are not included here.
