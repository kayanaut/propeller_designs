#!/usr/bin/env python3
"""Fill the mesh templates for one refinement level.   Usage: python3 scripts/configure_mesh.py [L0|L1|L2]

Domain 1.5 x 1.0 x 1.0 m. Only L0 has been meshed; L1 and L2 keep the same levels on a finer
background, so expect roughly 2.4x and 8x the L0 cell count.
"""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
# background cell (m), rotor surface, stator surface, rotorRegion, wakeRegion levels
levels = {'L0': (0.016, 6, 5, 4, 2), 'L1': (0.012, 6, 5, 4, 2), 'L2': (0.008, 6, 5, 4, 2)}
level = sys.argv[1] if len(sys.argv) > 1 else 'L0'
if level not in levels:
    raise SystemExit('level must be L0, L1, or L2')
h, rotor, stator, region, wake = levels[level]
nx, ny = round(1.5 / h), round(1.0 / h)
repl = {'@NX@': str(nx), '@NY@': str(ny), '@NZ@': str(ny), '@ROTOR_LEVEL@': str(rotor),
        '@STATOR_LEVEL@': str(stator), '@REGION_LEVEL@': str(region), '@WAKE_LEVEL@': str(wake)}
for name in ('blockMeshDict', 'snappyHexMeshDict'):
    text = (root / 'system' / f'{name}.template').read_text()
    for key, value in repl.items():
        text = text.replace(key, value)
    (root / 'system' / name).write_text(text)
print(f'Configured {level}: background {nx}x{ny}x{ny} ({h * 1e3:.0f} mm cells); levels rotor {rotor} '
      f'({h / 2**rotor * 1e3:.3f} mm), stator {stator} ({h / 2**stator * 1e3:.2f} mm), '
      f'rotorRegion {region} ({h / 2**region * 1e3:.1f} mm), wake {wake} ({h / 2**wake * 1e3:.0f} mm)')
