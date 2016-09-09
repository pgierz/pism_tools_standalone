#!/bin/bash

#grid file: 1200*1200
fgrid=grid_10km.nc

flag=2
if [ $flag -eq 1 ]; then
  echo
fi
# air temperature & precipitation
# source: COSMOS output T31
fname=LGM_temp2_tsurf_precip_annual.nc

echo "=====> interpolate surface air temperature to $fgrid "
cdo  -remapbil,$fgrid   $fname   remap.nc

echo "=====>  modify files into Pism readable files "
ncl  c2PismReadable_v1.ncl

echo "=====> output: forcing_lgm_v2.nc"
rm -f remap.nc
