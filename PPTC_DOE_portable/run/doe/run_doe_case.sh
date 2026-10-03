#!/bin/bash
# One DOE run on the M3 mesh.
# Usage: run_doe_case.sh RUN_ID J PITCH_DEG N_RPS NP
# Writes a row to results/results_doe.csv and keeps only light outputs in results/runs/RUN_ID.
set -o pipefail
RID=$1; J=$2; PITCH=$3; NRPS=$4; NP=${5:-}
if [ -z "$NP" ]; then NCPU=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN); TPC=$(lscpu 2>/dev/null | awk -F: '/Thread\(s\) per core/{print $2+0}' | head -1); NP=$(( NCPU / ${TPC:-1} )); fi
ROOT=${PPTC_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
CASE=$ROOT/runs/$RID
OUT=$ROOT/results/runs/$RID
[ -f $OUT/DONE ] || [ -f $OUT/FAILED ] && { echo "$RID already processed"; exit 0; }
FOAM_BASHRC=${FOAM_BASHRC:-/usr/lib/openfoam/openfoam2412/etc/bashrc}
command -v simpleFoam >/dev/null 2>&1 || source $FOAM_BASHRC >/dev/null 2>&1
command -v simpleFoam >/dev/null 2>&1 || { echo "OpenFOAM v2412 not found: set FOAM_BASHRC"; exit 2; }
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
MPIRUN="mpirun --bind-to none -np $NP"
[ "$(id -u)" = 0 ] && MPIRUN="mpirun --allow-run-as-root --bind-to none -np $NP"
D=0.25; MESH=M3; ENDTIME=1500
U=$(python3 -c "print(f'{-$J*$NRPS*$D:.6f}')")
OMEGA=$(python3 -c "import math;print(f'{2*math.pi*$NRPS:.6f}')")
read -r _ SMIN SMAX FEAT DISK WAKE ADDL NLAY < <(grep "^$MESH " $ROOT/template/meshlevels.txt)
T0=$(date +%s); status=ok

rm -rf $CASE; mkdir -p $CASE $OUT && cd $CASE || exit 1
cp -r $ROOT/template/system $ROOT/template/constant $ROOT/template/0.orig .
cp $ROOT/doe/sampleCloud system/
mkdir -p constant/triSurface   # empty dir is not kept by git
# geometry for this pitch (generated on the fly from the design-pitch surface)
if python3 -c "import sys; sys.exit(0 if abs($PITCH) < 1e-9 else 1)"; then
    cp $ROOT/stl/prop_pitch0.stl constant/triSurface/propeller.stl
else
    python3 $ROOT/doe/pitch_np.py $ROOT/stl/prop_pitch0.stl constant/triSurface/propeller.stl $PITCH > log.pitch 2>&1 || status=pitch_failed
fi
sed -e "s/@SMIN@/$SMIN/;s/@SMAX@/$SMAX/;s/@FEAT@/$FEAT/;s/@DISK@/$DISK/;s/@WAKE@/$WAKE/;s/@ADDLAYERS@/$ADDL/;s/@NLAYERS@/$NLAY/" \
    system/snappyHexMeshDict.tmpl > system/snappyHexMeshDict
sed -e "s/@NP@/$NP/" system/decomposeParDict.tmpl > system/decomposeParDict
sed -e "s/@ENDTIME@/$ENDTIME/g" system/controlDict.tmpl > system/controlDict
sed -i "s/omega .*;/omega           $OMEGA;/" constant/MRFProperties
sed -i "s/uniform (-2.00525 0 0)/uniform ($U 0 0)/g" 0.orig/U

if [ "$status" = ok ]; then
    blockMesh > log.blockMesh 2>&1 || status=blockMesh_failed
    surfaceFeatureExtract > log.surfaceFeatureExtract 2>&1
    decomposePar -force > log.decomposePar.mesh 2>&1
    $MPIRUN snappyHexMesh -parallel -overwrite > log.snappyHexMesh 2>&1 || status=snappy_failed
    $MPIRUN topoSet -parallel > log.topoSet 2>&1 || status=topoSet_failed
    $MPIRUN checkMesh -parallel -constant > log.checkMesh 2>&1
    grep -m1 "cells:" log.checkMesh | awk '{print $2}' > mesh_cells.txt
    # qualification gate: checkMesh must report "Mesh OK" (zero failed checks)
    { grep -E "cells:|Mesh non-orthogonality Max|Max skewness|Max aspect ratio|Mesh OK|Failed .* mesh checks" log.checkMesh; } > mesh_quality.txt
    if ! grep -q "^Mesh OK" log.checkMesh; then status=checkmesh_failed; fi
fi
T1=$(date +%s)
for p in processor*; do rm -rf $p/0; cp -r 0.orig $p/0; done
if [ "$status" = ok ]; then
    python3 $ROOT/force_watch.py $CASE & WATCH=$!
    $MPIRUN simpleFoam -parallel > log.simpleFoam 2>&1 || status=solver_failed
    kill $WATCH 2>/dev/null
fi
T2=$(date +%s)

# scalar results (KT, KQ, eta: mean of the last 100 iterations)
ALWAYS_HEADER=1 python3 $ROOT/post_case.py $CASE $J $NRPS $PITCH $MESH "$status" $((T1-T0)) $((T2-T1)) $NP \
    > $OUT/row.csv
flock $ROOT/results/.lock bash -c "[ -s $ROOT/results/results_doe.csv ] || head -1 $OUT/row.csv > $ROOT/results/results_doe.csv; tail -1 $OUT/row.csv >> $ROOT/results/results_doe.csv"

# light outputs: surface fields + fixed point cloud sample + histories + logs
if [ "$status" = ok ]; then
    reconstructParMesh -constant > log.reconstructParMesh 2>&1
    reconstructPar -latestTime > log.reconstructPar 2>&1
    foamToVTK -latestTime -no-internal -patches propeller > log.foamToVTK 2>&1
    postProcess -latestTime -func sampleCloud > log.sampleCloud 2>&1
    cp -r VTK postProcessing $OUT/ 2>/dev/null
fi
cp log.* mesh_cells.txt mesh_quality.txt $OUT/ 2>/dev/null
cp constant/triSurface/propeller.stl $OUT/ 2>/dev/null
echo "$RID J=$J pitch=$PITCH n=$NRPS status=$status mesh=$((T1-T0))s solve=$((T2-T1))s" > $OUT/summary.txt
# free disk: full decomposed/reconstructed fields are not kept
cd $ROOT && rm -rf $CASE
[ "$status" = ok ] && touch $OUT/DONE || echo "$status" > $OUT/FAILED
cat $OUT/summary.txt
[ "$status" = ok ]
