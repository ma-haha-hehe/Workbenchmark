# Primitive parts

These standalone MuJoCo XML scenes cover the two part types in the benchmark:
`brick_2x2` and `brick_4x2`. Each scene includes one free body and a floor.
No external mesh, texture, or robot asset is required. Units are metres and kilograms.
Visual and collision geometry use the same primitives.

Open a scene with `python -m mujoco.viewer --mjcf=parts/brick_2x2.xml` from the repository root.
Copy the part body into another MJCF world to reuse it; give each instance a unique body name.
The body origin is 18.6 mm above its underside. Body height is 19.2 mm, excluding studs.
The body outline leaves 0.2 mm clearance per nominal axis between adjacent bricks;
the 16 mm stud pitch and task coordinates are unchanged. This clearance is not
a manufacturer measurement.

These are simplified, self-authored hollow rigid-body models, not manufacturer CAD.
Wall, tube, stud, mass and friction parameters are approximations. Plastic deformation
and clutch force have not been calibrated. Unsupported cantilevers may fall;
resting-contact validation does not demonstrate successful robotic assembly.
This variant includes compliant internal ribs and lead-ins. The fit uses contact forces and friction, without attachment constraints. Copy the asset meshes as well as the body when reusing this model. Parameters are uncalibrated; see manifest.json. Generate this variant with --contact-profile plastic.

`manifest.json` records source provenance, instance counts, file hashes and the
one-second resting-contact check. Regenerate with robot_korea's
`scripts/export_workbenchmark_parts.py --repository ../Workbenchmark --output ../Workbenchmark/parts --contact-profile plastic`.
Original task layouts are unchanged.

The generated models retain robot_korea's Apache-2.0 license; see LICENSE and NOTICE.
This notice applies to this parts directory and does not assign a license to the
original benchmark task YAML files.

The internal fit uses six-dimensional contact: sliding friction 0.3,
torsional friction length 1 mm, and rolling friction length 0.05 mm.
`axial_fixture_results.json` records aligned insertion at 3 N and pullout
at 3.0 N (2x2) / 5.8 N (4x2). These are simulation fixture results, not
measurements of manufactured plastic parts or robot assembly success.
Run `python parts/validate.py` to check the inventory, file hashes,
compiled contact parameters and one-second resting dynamics.
