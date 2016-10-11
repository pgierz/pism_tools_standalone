#! /bin/bash

gebco=/scratch/users/egowan/pism/GEBCO/gebco_08_1m.grd

ice_thickness=80000_thickness
ice_topography=80000_topo
base_topography_difference="topo_difference_80000" # difference from modern topography
base_topograph_difference_reference="topo_difference_0" # reference time

sample_modern_topo=false # change to true if you want to change the grid (i.e. different grid spacing, area)
filter_width=50 # in km
filter_type=m

north=85.
south=30.
west=-180.
east=0.

lat_spacing=0.25
long_spacing=0.5


# python script to create x,y file with the above information
# works as long as you don't go over the date line
cat << END_CAT > create_xy.py
num_x =int(( (${east} - ${west}) / ${long_spacing})) + 2
num_y = int(( (${north} - ${south}) / ${lat_spacing})) + 2

for x in xrange(1, num_x):
    for y in xrange(1, num_y ):
        print ${west}+(x-1)*${long_spacing}, ${south}+(y-1)*${lat_spacing}

END_CAT

python create_xy.py > ll_file.txt


# longitude file
awk '{print $1, $2, $1}' ll_file.txt > temp

x_name=x
y_name=y
z_name="longitude [degree_east]" # always include units
z_scale="1"
z_offset="0" # applied after scaling
z_invalid="-181" # value for areas without data
title="longitude" # title for the data
remark="longitude"

xyz2grd temp -Glong.nc -R${west}/${east}/${south}/${north} -I${long_spacing}/${lat_spacing} -D${x_name}/${y_name}/"${z_name}"/${z_scale}/${z_offset}/${z_invalid}/"${title}"/"${remark}" -di${z_invalid}  # last thing because for some reason the -D option is not working

ncrename -v z,lon  long.nc

# latitude file
awk '{print $1, $2, $2}' ll_file.txt > temp

x_name=x
y_name=y
z_name="latitude [degree_north]" # always include units
z_scale="1"
z_offset="0" # applied after scaling
z_invalid="-91" # value for areas without data
title="latitude" # title for the data
remark="latitude"

xyz2grd temp -Glat.nc -R${west}/${east}/${south}/${north} -I${long_spacing}/${lat_spacing} -D${x_name}/${y_name}/"${z_name}"/${z_scale}/${z_offset}/${z_invalid}/"${title}"/"${remark}" -di${z_invalid}  # last thing because for some reason the -D option is not working

ncrename -v z,lat  lat.nc



awk '{print $2-360, 90-$1, -$3}' ${ice_thickness} > temp

x_name=x
y_name=y
z_name="land_ice_thickness [m]" # always include units
z_scale="1"
z_offset="0" # applied after scaling
z_invalid="0" # value for areas without data
title="thk" # title for the data
remark="Ice thickness NAICE 80000 yr BP"

xyz2grd temp -Gthickness.nc -R${west}/${east}/${south}/${north} -I${long_spacing}/${lat_spacing} -D${x_name}/${y_name}/"${z_name}"/${z_scale}/${z_offset}/${z_invalid}/"${title}"/"${remark}" -di${z_invalid} # last thing because for some reason the -D option is not working

ncrename -v z,${title}  thickness.nc


# create deformed base topography


if [ "${sample_modern_topo}" = true ] 
then
	grdfilter ${gebco} -Gsampled_topography.nc -R${west}/${east}/${south}/${north} -I${long_spacing}/${lat_spacing} -D4 -F${filter_type}${filter_width} # median filter, will remove extreme changes
fi

paste ${base_topograph_difference} ${base_topograph_difference_reference} | awk '{print $2-360, 90-$1, $3-$6}' > temp


x_name=x
y_name=y
z_name="bedrock surface elevation [m]" # always include units
z_scale="1"
z_offset="0" # applied after scaling
z_invalid="-99999" # value for areas without data
title="topg" # title for the data
remark="bedrock topography"



xyz2grd temp -Gtopg_temp.nc -R${west}/${east}/${south}/${north} -I${long_spacing}/${lat_spacing} -D${x_name}/${y_name}/"${z_name}"/${z_scale}/${z_offset}/${z_invalid}/"${title}"/"${remark}" -di${z_invalid} # last thing because for some reason the -D option is not working


grdmath sampled_topography.nc topg_temp.nc ADD = topg.nc

ncatted -O -a long_name,z,o,c,"bedrock surface elevation" topg.nc
ncatted -O -a units,z,o,c,"m" topg.nc
ncrename -v lon,x topg.nc
ncrename -v lat,y topg.nc
ncrename -v z,topg topg.nc


#


x_name=x
y_name=y
z_name="usurf [m]" # always include units
z_scale="1"
z_offset="0" # applied after scaling
z_invalid="-99999" # value for areas without data
title="usurf" # title for the data
remark="Ice topography"


xyz2grd ${ice_topography} -Gtopography.nc -R${west}/${east}/${south}/${north} -I${long_spacing}/${lat_spacing} -D${x_name}/${y_name}/"${z_name}"/${z_scale}/${z_offset}/${z_invalid}/"${title}"/"${remark}" -di${z_invalid} # last thing because for some reason the -D option is not working

ncrename -v z,usurf  topography.nc



ncks  --overwrite topg.nc combined.nc
ncks  -A thickness.nc combined.nc
ncks  -A long.nc combined.nc
ncks  -A lat.nc combined.nc

ncdump -h combined.nc

grd2xyz topg.nc > dumped_base_topo.txt
