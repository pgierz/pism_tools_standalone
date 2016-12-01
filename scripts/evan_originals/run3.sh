#! /bin/bash

pism_bin="/scratch/users/egowan/pism/bin"

PATH=${PATH}:${pism_bin}
export PATH

# set number of processors
processors=3

# pism options
input_file="ice_files/combined.nc" # input netcdf file of the geometry of the problem
bootstrap="-bootstrap" # "This term describes the creation, by
		       # heuristics and highly-simplified models, of
		       # the mathematical initial conditions required
		       # for a deterministic, time-dependent ice
		       # dynamics model.", should be on if using an
		       # input grid
x_dimension="131" # number of grid points in the x direction (number
		  # of elements is 1 less)
y_dimension="113" # number of grid points in the y direction (number
		  # of elements is 1 less)
z_dimension="101" # number of grid points in the z direction (number
		  # of elements is 1 less)
bedrock_thermal_z_dimension="11" # number of grid points in the bedrock z direction   required to be >1 to use the bedrock thermal model
z_spacing=equal # by default, it is "quadratic" (i.e. higher resolution near the base)
maximum_height=10000 # maximum height allowed in the z direction, should be greater than the expected highest point
maximum_depth=2000 # maximum depth of the thermal bedrock layer
skip_flags="-skip  -skip_max 10" # flags related to adaptive time stepping. skip_max sets the maximum amount of sub-steps between major time steps

# parameters for atmosphere, see PISM climate forcing manual (section 6) for options

atmosphere_type="given,lapse_rate" # tells the program that we are providing atmospheric forcing from a file, and to use a lapse rate
atmosphere_file="-atmosphere_given_file forcing/combined.nc" # input file for atmospheric forcing
atmosphere_period="-atmosphere_given_period 1" # Input atmosphere is read in as a periodic variable of  #years
precip_lapse_rate="-precip_lapse_rate 1" # preciptation lapse rate, in units of m/yr/km
atmosphere_lapse_rate_file="-atmosphere_lapse_rate_file ice_files/combined.nc" # file that contains the lapse rate values, basically refering to the surface altitude

atmosphere_params="-atmosphere ${atmosphere_type} ${atmosphere_file} ${atmosphere_period} ${precip_lapse_rate} ${atmosphere_lapse_rate_file}"

# surface boundary forcing parameters, see PISM climate forcing manual (section 5) for options
surface=pdd # surface boundary condition temperatures using positive
	    # degree day scheme. By default, uses scheme developed by
	    # Calov and Greve (2005) and EISMINT-Greenland

surface_params="-surface ${surface}"

# ocean parameters, see section 7 of the PISM climate forcing manual

ocean="constant" # default value, ocean conditions are constant through time

ocean_params="-ocean ${ocean}"

# ice shelf calving parameters, see section 8.3 of the PISM manual 

#calving="-calving ocean_kill" # kills off any place with elevation below zero that are ice free (defined by a mask of ice thickness)
#ocean_kill_file="-ocean_kill_file ${input_file}"
#calving_params="${calving} ${ocean_kill_file}"

calving="-calving thickness_calving"
calving_thickness="-thickness_calving_threshold 200"
calving_params="${calving} ${calving_thickness}"

# Stress model, see section 6.1 of the PISM manual

stress_balance="-stress_balance ssa+sia" # use hybrid model
sia_stress_enhancement_factor="-sia_e 10"  # scaling parameter for the strain rate tensor in the SIA "flow law"

stress_params="${stress_balance} ${sia_stress_enhancement_factor}"

# simulation time settings
start_time="0" # in years

end_time="30000" # 

# parameters related to saving

# base output file name
file_out=results_$( echo ${sia_stress_enhancement_factor} | awk '{print $2}').nc

dt=50 # save ever time value of this


# GIA parameters

#gia_model="-bed_def lc"

# Hydrology parameters

#hydrology_model="-hydrology routing"


#extra files to modify PISM to calculate at these exact times


extra_file1="-extra_file  ex_${file_out}"
extra_times1="-extra_times  0:${dt}:${end_time}" # do full saves every interval, dt
extra_variables1="-extra_vars lon,lat,thk,topg,usurf,climatic_mass_balance,ice_surface_temp,air_temp,precipitation,smelt,srunoff,saccum"
extra_params1="${extra_file1} ${extra_times1} ${extra_variables1}"

extra_file2="-extra_file test.nc"
extra_times2="-extra_times 0:daily:1" # do full saves every interval, dt
extra_variables2="-extra_vars thk,precipitation"
#extra_params2="${extra_file2} ${extra_times2} ${extra_variables2}"

# save scalar parameters

ts_file="-ts_file  ts_${file_out}"
ts_times="-ts_times  0:${dt}:${end_time}"

ts_file_params="${ts_file} ${ts_times}"

# output files, PISM doesn't calculate exactly at these times, but will interpolate between times that are calculated

output_file="-o ${file_out}"
output_verbosity="-o_size big" # big means that all parameters are saved

output_params="${output_file} ${output_verbosity}"




mpirun -np  ${processors}  \
pismr -i ${input_file} ${bootstrap}   \
       -Mx ${x_dimension}  -My  ${y_dimension}  -Mz  ${z_dimension}  -Mbz ${bedrock_thermal_z_dimension} -z_spacing  ${z_spacing}  -Lz ${maximum_height} -Lbz  ${maximum_depth} ${skip_flags}  \
       ${atmosphere_params}      \
       ${surface_params}        \
       ${ocean_params}  ${calving_params} \
       ${stress_params} ${gia_model}  \
       -ys ${start_time} -ye ${end_time}  \
       ${extra_params1}  \
       ${extra_params2}   \
       -ts_file  ts_${filout} ${ts_file_params}  \
       ${output_params}
