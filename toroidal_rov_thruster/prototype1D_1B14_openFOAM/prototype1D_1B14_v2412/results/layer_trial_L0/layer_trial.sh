#!/bin/bash
# Layer trial on a copy of the design B L0 mesh. The main case is not touched.
set -e
C=/home/kaya/Desktop/LX/thruster/drone_propeller_designs/toroidal_rov_thruster/prototype1D_1B14_openFOAM/prototype1D_1B14_v2412
S=/tmp/claude-1000/-home-kaya-Desktop-LX-thruster-drone-propeller-designs/54fbb03d-ae28-47fa-a8e3-756f6ccd1a33/scratchpad
L=$S/layer_trial

grep -q "Mesh OK." "$C/log.checkMesh" || { echo "main case has no passing mesh"; exit 1; }
rm -rf "$L" && mkdir -p "$L"
cp -r "$C/system" "$C/constant" "$L/"
cp "$S/snappyHexMeshDict.layers" "$L/system/"
cd "$L"
openfoam2412 -c '
    /usr/bin/time -f "layers elapsed %E, peak %M kB" \
        snappyHexMesh -dict system/snappyHexMeshDict.layers -overwrite > log.snappyLayers 2>&1
    checkMesh > log.checkMesh 2>&1
' || true
tail -1 log.snappyLayers
grep -B2 -A8 "overall thickness" log.snappyLayers | tail -12
grep -E "Layer mesh|Finished meshing|FOAM FATAL" log.snappyLayers | tail -3
grep -E "cells:|prisms|non-orthogonality Max|skewness|Failed|Mesh OK" log.checkMesh
