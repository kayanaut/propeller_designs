#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
levels={'L0':(0.008,5,4,5),'L1':(0.006,6,5,6),'L2':(0.004,7,6,7)}
level=sys.argv[1] if len(sys.argv)>1 else 'L0'
if level not in levels: raise SystemExit('level must be L0, L1, or L2')
h,rl,dl,gl=levels[level]
nx=round(0.60/h); ny=round(0.40/h); nz=ny
repl={'@NX@':str(nx),'@NY@':str(ny),'@NZ@':str(nz),'@ROTOR_LEVEL@':str(rl),'@DUCT_LEVEL@':str(dl),'@GAP_LEVEL@':str(gl)}
for src,dst in [(root/'system'/'blockMeshDict.template',root/'system'/'blockMeshDict'),(root/'system'/'snappyHexMeshDict.template',root/'system'/'snappyHexMeshDict')]:
    s=src.read_text()
    for a,b in repl.items(): s=s.replace(a,b)
    dst.write_text(s)
print(f'Configured {level}: background {nx}x{ny}x{nz}, rotor={rl}, duct={dl}, gap={gl}')

