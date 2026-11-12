# Build tools

These are the scripts the mod's generated files came from. They are working notes rather than a
polished pipeline: paths and file names inside them are hard-coded to the original working folder.

| Script | What it does |
|---|---|
| `find_positions.py` | Casts rays from the driver's eye into the car's interior meshes to find a gauge position that is fully visible for each mounting |
| `build_pod_mesh.py` | Builds one gauge + pod mesh (Blender `bpy`), ray-casting each of the pod's 40 columns onto the interior surface |
| `export_dae.py` | Writes all pod, bezel and screen meshes into the Collada file |
| `gen_jbeam.py` | Generates the Covet part file (all mountings, finishes, sliders) |
| `fit_check_render.py` | Software render of the car interior with the gauges, used to check the fit |
| `bake_faceplates.html` | Bakes the printed face textures from the display page's own drawing code |

The placement and pod-shaping steps need the car's interior meshes extracted from the game's own
`covet.dae`. Those are BeamNG's files and are not included here.
