#!/usr/bin/env bash

expid=$1
INDIR=input
OUTDIR=output
RESDIR=restart
SCRIPTDIR=scripts

for d in $INDIR $OUTDIR $RESDIR $SCRIPTDIR
do
    mkdir -pv $expid/$d
done
