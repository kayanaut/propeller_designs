#!/usr/bin/env python3
from pathlib import Path
import math, struct, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'geometry'; DST=ROOT/'constant'/'triSurface'; DST.mkdir(parents=True, exist_ok=True)

def vertices(path):
    b=path.read_bytes()
    if len(b)>=84:
        n=struct.unpack('<I',b[80:84])[0]
        if 84+50*n==len(b):
            for i in range(n):
                vals=struct.unpack('<12fH',b[84+50*i:134+50*i])
                for j in (3,6,9): yield vals[j:j+3]
            return
    text=b.decode('utf-8',errors='ignore')
    for line in text.splitlines():
        s=line.split()
        if len(s)==4 and s[0].lower()=='vertex': yield tuple(map(float,s[1:]))

def check(name, kind):
    p=SRC/name
    if not p.exists(): raise SystemExit(f'MISSING: {p}')
    vs=list(vertices(p))
    if len(vs)<12: raise SystemExit(f'INVALID STL (too few vertices): {p}')
    if not all(math.isfinite(q) for v in vs for q in v): raise SystemExit(f'INVALID STL (non-finite coordinate): {p}')
    lo=[min(v[i] for v in vs) for i in range(3)]; hi=[max(v[i] for v in vs) for i in range(3)]
    span=[hi[i]-lo[i] for i in range(3)]
    radial=max(abs(q) for v in vs for q in v[1:])
    if kind=='rotor' and not (0.045 <= radial <= 0.052): raise SystemExit(f'Rotor radial extent {radial:.6g} m is inconsistent with 100 mm diameter')
    if kind=='duct' and not (0.052 <= radial <= 0.075): raise SystemExit(f'Duct radial extent {radial:.6g} m is implausible for 104 mm throat')
    if max(span)>0.20: raise SystemExit(f'{name} likely not in metres; spans={span}')
    shutil.copy2(p,DST/name)
    print(f'{name}: vertices={len(vs)}, bounds={lo}..{hi}, OK')

check('rotor_1B14.stl','rotor'); check('duct_1B14.stl','duct')

