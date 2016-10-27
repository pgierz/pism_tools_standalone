#!/usr/bin/env bash

expid=$1
INDIR=input
OUTDIR=output
RESDIR=restart
SCRIPTDIR=scripts
WORKDIR=work
BINDIR=bin

for d in $INDIR $OUTDIR $RESDIR $SCRIPTDIR $WORKDIR $BINDIR
do
    mkdir -pv $expid/$d
done

cat ${HOME}/palmod_pism_standalone/scripts/run_script_template.sh |sed s+@EXPNAME@+"${expid}"+g > $expid/${SCRIPTDIR}/${expid}.run
