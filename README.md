# Workbenchmark

400 brick assembly tasks organized into four tiers of 100 tasks each.
The task files contain 2,009 part instances: 1,056 `brick_2x2` and 953 `brick_4x2`.

## Contents

- `benchmark_tasks/`: original initial layouts and finished assemblies.
- `parts/`: standalone MuJoCo scenes for both part types, source provenance,
  dimensions and license notices. No external mesh assets are required.

Each task YAML contains `blocks` for the finished assembly and `initial_blocks`
for the loose parts. Match instances by `name`, not by list order. Positions use
metres; the supplied upright rotations use degrees. The legacy initial Z value
is 0.0495 m and must be converted when a simulator uses a different body origin.

## Run with robot_korea

Clone [robot_korea](https://github.com/ma-haha-hehe/robot_korea) alongside this
repository. The integration tools are under active local validation and are not
all available on its published default branch yet.

From a checkout containing the Workbenchmark integration:

```bash
source enter_sim_env.sh
export PYTHONPATH="$PWD/src/mj_bridge:$PYTHONPATH"
python scripts/import_workbenchmark.py --repository ../Workbenchmark \
  --output runs/workbenchmark-recorded --initial-layout recorded
python -m mj_bridge.benchmark_cli run \
  --product runs/workbenchmark-recorded/tier1_task_001.yaml \
  --connection-mode physics --contact-profile plastic --executor oracle-baseline --headless --robot-base-x=-.05 \
  --output-dir runs/workbenchmark-tier1
```

The importer preserves relative goal geometry and recorded initial XY/yaw.
It translates the finished assembly into the robot's assembly frame and records
that transform and source hashes. It does not alter the original task files.

## Validation status

These resources do not certify successful robotic assembly of all 400 tasks.
The generated parts use a compliant stud fit with continuous insertion bevels
and Coulomb friction. The parameters are a simulation approximation, without
measured material calibration. The plastic profile must be enabled explicitly.
Some assemblies may require revised geometry or a different grasp strategy. Static geometry, gravity settling and actual robot execution
are separate checks; only complete execution with valid contacts counts as an
assembly success. Real GPU perception and physical robot operation are not validated.

The generated files under `parts/` retain their source project's Apache-2.0 license.
That license statement does not assign a new license to the original task YAMLs.
