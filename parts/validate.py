"""Check published part files and their task inventory, without running assembly."""
# SPDX-License-Identifier: Apache-2.0
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
import yaml


def validate():
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / 'manifest.json').read_text())
    tasks = sorted((here.parent / 'benchmark_tasks').glob('*.yaml'))
    inventory = Counter()
    for task in tasks:
        data = yaml.safe_load(task.read_text())
        for block in data['blocks']:
            prefix = block['name'].split('_brick_')[0]
            inventory['brick_' + prefix] += 1
    if len(tasks) != manifest['task_count']:
        raise ValueError('task count differs from the part manifest')
    if inventory != Counter({p['type']: p['instances'] for p in manifest['parts']}):
        raise ValueError('part types or counts differ from the task inventory')
    parameters = manifest['contact_parameters']
    fixture = json.loads((here / 'axial_fixture_results.json').read_text())
    if (fixture['parameters'] != parameters
            or fixture['source_sha256'] != manifest['plastic_contact_sha256']):
        raise ValueError('axial fixture uses different contact parameters or source')
    if ({row['part'] for row in fixture['results']} != set(inventory)
            or not all(row['passed'] for row in fixture['results'])):
        raise ValueError('axial fixture does not cover both published part types')
    for part in manifest['parts']:
        path = here / part['mjcf']
        if hashlib.sha256(path.read_bytes()).hexdigest() != part['sha256']:
            raise ValueError(f'part checksum mismatch: {path.name}')
        xml = ET.parse(path)
        if xml.findall('.//include') or any(node.get('file') for node in xml.iter()):
            raise ValueError(f'part is not self-contained: {path.name}')
        model = mujoco.MjModel.from_xml_path(str(path))
        if model.neq or model.nq != 7:
            raise ValueError(f'expected one unconstrained free body: {path.name}')
        fit = model.geom_priority == 2
        expected_friction = [parameters['sliding_friction'],
                             parameters['torsional_friction_m'],
                             parameters['rolling_friction_m']]
        if (not np.any(fit)
                or not np.all(model.geom_condim[fit] == parameters['contact_dimensions'])
                or not np.allclose(model.geom_friction[fit], expected_friction, rtol=0, atol=1e-12)
                or not np.allclose(model.geom_solref[fit],
                    [parameters['contact_time_constant_s'], parameters['damping_ratio']],
                    rtol=0, atol=1e-12)):
            raise ValueError(f'compiled contact parameters differ from manifest: {path.name}')
        body = model.body(part['type']).id
        if abs(float(model.body_mass[body]) - part['mass_kg']) > 1e-9:
            raise ValueError(f'mass differs from manifest: {path.name}')
        state = mujoco.MjData(model)
        peak = 0.
        for _ in range(round(1. / model.opt.timestep)):
            mujoco.mj_step(model, state)
            if state.ncon:
                peak = max(peak, float(-np.min(state.contact.dist)))
        if (not np.isfinite(state.qpos).all() or peak > .0005
                or abs(state.xpos[body, 2] - .0186) > .001
                or state.xmat[body, 8] < np.cos(np.deg2rad(1.))):
            raise ValueError(f'resting contact failed: {path.name}')
        print(f'{part["type"]}: checksum, free-body dynamics and resting contact passed')
    print(f'{len(tasks)} task inventories checked; robotic assembly was not tested')


if __name__ == '__main__':
    validate()
