#!/usr/bin/bash -l
################################################################################
# BATCH HEADERS
################################################################################
#SBATCH --job-name=PI_C31_R
#SBATCH --get-user-env
#SBATCH -p mpp
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=36
#SBATCH --exclusive
#SBATCH --time=00:60:00
#SBATCH --output=greenland_pi_cosmosT31_remap_%j.log
#SBATCH --error=greenland_pi_cosmosT31_remap_%j.log
#SBATCH --mail-type=FAIL
################################################################################
ulimit -s unlimited
echo "This PISM run was perfomed on $HOSTNAME on $(date)"
echo "Running in $(pwd)"
echo "sourcing..."
source /etc/bashrc && echo "done!"
################################################################################
#           Parallel Ice Sheet Model    R U N   S C R I P T      (Ollie version)
################################################################################

################################################################################
# NOTE:                                                                        #
#                                                                              #
# This script has been put together by working through the examples            #
# found in the PISM handbook and successively attempting to generalize         #
# the options that are presented. Unfortunately, the handbook does not         #
# provide examples for every single configuration combination, so it is        #
# likely that the options that can be set via this script are not complete.    #
#                                                                              #
#                                                                              #
# It is therefore highly recommended to read the entire script and             #
# understand it first, work through the handbook examples *BY HAND*,           #
# and then rework them with this script to see how everything can be           #
# done                                                                         #
#                                                                              #
# -----------------------------------------------------------------------------#
# Under construction:                                                          #
# Paul J. Gierz, Fri Jul 22 14:36:42 2016                                      #
# Paul J. Gierz, Mon Jul 26 10:12:41 2016                                      #
# Paul J. Gierz, Tue Jul 26 16:30:32 2016                                      #
# Paul J. Gierz, Wed Jul 27 10:59:38 2016                                      #
# Paul J. Gierz, Fri Oct  7 10:52:57 2016                                      #
# Paul J. Gierz, Wed Oct 12 15:44:25 2016                                      #
# Paul J. Gierz, Fri Nov  4 10:49:18 2016                                      #
# -----------------------------------------------------------------------------#
# The version saved on Nov 4 is shared with the paleodyn group.                #
# Paul J. Gierz, Fri Nov  4 10:49:18 2016                                      #
# -----------------------------------------------------------------------------#
# AWI Bremerhaven                                                              #
################################################################################

################################################################################
# TODOs                                                                        
#
# * DONE SBATCH headers?
# * DONE Script headings and sections
# * TODO organize script in such a way that it makes sense
# * TODO separate parsing of options from setting of options. The user
#        doesn't need to see everything
# * TODO How to handle resolution with different ice domains?
#
################################################################################

icemod=pismr

########################################
# DIRECTORY STRUCTURES
########################################

expid=@EXPNAME@
# Directories

export homedir=/work/ollie/pgierz/pism_standalone/
export scriptdir=${homedir}/${expid}/scripts
export outdir=${homedir}/${expid}/outdata
export indir=${homedir}/${expid}/input
export logdir=${homedir}/${expid}/log
export bindir=/work/ollie/pgierz/pism0.7/bin/
export workdir=${homedir}/${expid}/work

pooldir=/work/ollie/pgierz/pool_pism/
subpool=examples_greenland

numproc=72			# Number of processors to use
execution_command="/global/opt/slurm/default/bin/srun --mpi=pmi2"


# Time Control
start_year=-10000
end_year=0
step_year=100

# Go to scriptdir to start
cd $scriptdir

# NEEDED_FILES_LIST
NEEDED_FILES=""

if [ ! -f ${expid}.date ]
then
    echo "no date file found!"
    run_number=0
else
    run_number=$(cat ${expid}.date)
fi


if [[ $run_number -eq 0 ]]
then
    bootstrap=1
    # Input File Name:
    input_file_name=pism_Greenland_5km_v1.1.nc
    current_year=$start_year
    echo "FIRST YEAR"
else
    bootstrap=0
    # Input File name needs to be the output of the last run
    input_file_name=$(ls ${outdir}/${expid}_${icemod}_main_*.nc | tail -1)
    current_year=$( expr ${start_year} + ${step_year} \* ${run_number} )
    echo "RESTARTING for $current_year"
fi

current_end=$( expr ${current_year} + ${step_year} )

if [[ $current_year -gt ${end_year} ]]
then
    echo "EXPERIMENT FOR ${expid} OVER!"
    exit
fi
      
if [[ $bootstrap -eq 1 ]]
then
    bootstrap_opt="-bootstrap"
fi

NEEDED_FILES="$NEEDED_FILES $input_file_name"

#############################################
#                     RESOLUTION OPTIONS    
#############################################


res=low				# Pick between: very_low (40km), low (20km), med (10km), high (5km)

if [[ $res == "very_low" ]]
then
    # PG: untested...
    xres_ice=38
    yres_ice=72
    zres_ice=101
    bz=11
    skip_max=5
elif [[ $res == "low" ]]
then
    xres_ice=76
    yres_ice=141
    zres_ice=101
    bz=11				# TODO: find a better name for this variable
    skip_max=10
elif [[ $res == "med" ]]
then
    xres_ice=151
    yres_ice=281
    zres_ice=201
    bz=21
    skip_max=20
elif [[ $res == "high" ]]
then
    xres_ice=301
    yres_ice=561
    zres_ice=201
    bz=21
    skip_max=40
else
    echo "$0 Error: A resolution was selected that is not predefined"
    exit 42
    
fi


z_spacing_equal=1		# 1: True, 0:False
if [[ $z_spacing_equal -eq 1 ]]
then
    z_spacing_opt=equal
fi
Lz=4000
Lbz=2000

resolution_opt="-Mx $xres_ice -My $yres_ice -Mz $zres_ice -Mbz $bz -z_spacing $z_spacing_opt -Lz $Lz -Lbz $Lbz -skip -skip_max $skip_max "

#########################################################
# Regrid (What is this?)
#########################################################
regrid=0			# True 1; False 0
if [[ $regrid -eq 1 ]]
then
    regrid_file=PLACEHOLDER	# PG: file to regrid from goes here
    regrid_vars=litho_temp,thk,enthalpy,tillwat,bmelt # PG: Copied from example
    regrid_opt="-regrid_file $regrid_file -regrid_vars $regrid_vars"
else
    regrid_opt=""
fi

###############################################################
#                     COUPLING OPTIONS                        
###############################################################

# This section is designed to replicate the spinup.sh "coupler = 'blah
# blah'" output.
# Paul J. Gierz, Wed Jul 27 10:59:32 2016


######################
# Bedrock Deformation
######################

# Which bedrock deformation model to use.
# Allowed values: none, iso, lc
bed_def="lc"
case $bed_def in
    "none")
	bed_def_opt=""
	;;
    "iso")
	bed_def_opt="-bed_def iso"
	;;
    "lc")
	bed_def_opt="-bed_def lc"
	;;
    *)
	echo "Unknown bed_def option selected, exiting..."
	exit 42
esac

###############################
# Atmosphere >--|> Ice Forcings
###############################
atmosphere="searise_greenland"
use_input=1			# True 1; False 0
# Uses the input file for the forcing processes in atmosphere

case $atmosphere in
    "none")
	echo "No atmosphere coupling is used!"
	atmo_flag=""
	atmo_flag_extra=""
	;;
    "given")
	echo "Atmosphere --> Ice coupling type being used: |>>> given <<<|"
	atmo_flag=" -atmosphere given"
	extra_file=${indir}/atmo_given_file.nc
	atmo_flag_extra=" -atmosphere_given_file $extra_file"
	;;
    "yearly_cycle")
	echo "Atmosphere --> Ice coupling type being used: |>>> yearly_cycle <<<|"
	atmo_flag=" -atmosphere yearly_cycle"
	extra_file=${indir}/atmo_yearly_cycle_file.nc
	atmo_flag_extra=" -atmosphere_yearly_cycle_file ${extra_file}"
	echo "Testing only so far..."
	;;
    "searise_greenland")
	echo "Atmosphere --> Ice coupling type being used: |>>> searise_greenland <<<|"
	atmo_flag=" -atmosphere searise_greenland"
	if [[  ${use_input} != 1 ]]
	then
	    extra_file=${indir}/atmo_searise_greenland_file.nc
	    atmo_flag_extra=" -atmosphere_searise_greenland_file $extra_file"
	fi
	;;
    "one_station")
	echo "Atmosphere --> Ice coupling type being used: |>>> one_station <<<|"
	echo "Atmosphere coupler for this type not implemented, please go whack Paul over the head to fix this..."
	;;
    *)
	echo "ERROR: Atmosphere --> Ice coupler for $atmosphere unknown and not in standard types described in PISM manual. Go talk to Paul, he will figure it out..."
esac
NEEDED_FILES="$NEEDED_FILES $extra_file"

# atmosphere_modifiers
scalar_temperature_offsets=0	# True 1; False 0
if [[ $scalar_temperature_offsets == 1 ]]
then
    atmo_flag="${atmo_flag},delta_T"
    # The file needs to be in Kelvin!
    atmosphere_delta_T_file=${indir}/atmo_delta_T_file.nc
    scalar_temperature_offsets_opts=" -atmosphere_delta_T_file $atmosphere_delta_T_file"
    atmo_modifier_opts="$atmo_modifier_opts $scalar_temperature_offsets_opts"
fi

scalar_precipitation_offsets=0	# True 1; False 0
if [[ $scalar_precipitation_offsets == 1 ]]
then
    atmo_flag="${atmo_flag},delta_P"
    atmosphere_delta_P_file=${indir}/atmo_delta_P_file.nc
    scalar_temperature_offsets_opts=" -atmosphere_delta_P_file $atmosphere_delta_P_file"
    atmo_modifier_opts="$atmo_modifier_opts $scalar_temperature_offsets_opts"
fi

paleo_precipitation=0 		# True 1; False 0
if [[ $paleo_precipitation == 1 ]]
then
    atmo_flag="${atmo_flag},paleo_precip"
    extra_file=${indir}/paleo_precip_file.nc
    paleo_precip_opts=" -atmosphere_paleo_precip_file $extra_file"
    atmo_modifier_opts="$atmo_modifier_opts $paleo_precip_opts"
fi

# The following atmospheric modifiers are not (yet) implemented in the
# run script logic, but can be set with command switches at the end if
# the command string is modified at the end of the runscript:

# scalar_precipitation_scaling
# lapse_rate
# anomaly

# Full Atmosphere command
atmo_command="${atmo_flag} ${atmo_flag_extra} ${atmo_modifier_opts}"

#########################
# Surface Process Models
#########################

surface_opt="simple"
case $surface_opt in
    "simple")
	surface_command=" -surface simple"
	;;
    "given")
	surface_given_file=${input_file_name}
	surface_command=" -surface given -surface_given_file $surface_given_file"
	;;
    "elevation")
	echo "surface type for $surface_opt not implemented..."
	;;
    "pdd")
	# this one is complicated...
	pdd_sd_file=pdd_sd_file.nc
	# pdd_sd_period (years?)
	# pdd_sd_reference_year
	surface_command=" -surface pdd "
	;;
    "pik")

	echo "surface type for $surface_opt not implemented..."
	;;
    *)
	echo "unknown surface opt provided."
esac


###########################
# Ocean >--|> Ice Forcings
###########################
ocean="constant"
use_input=1			# True 1; False 0
# Uses the input file for the forcing processes in ocean

case $ocean in
    "constant")
	echo "Ocean --> Ice coupling being used is |>> constant <<| (This is the default choice)"
	ocean_flag="-ocean constant"
	;;
    "given")
	echo "Ocean --> Ice coupling being used is |>> given <<|"
	ocean_flag="-ocean given"
	if [[ ${use_input} != 1 ]]
	then
	    extra_file=${indir}/ocean_given_file.nc
	    ocean_flag_extra=" -ocean_given_file $extra_file"
	fi	
	;;
    "pik")
	echo "Ocean --> Ice coupling being used is |>> pik <<|"
	ocean_flag="-ocean pik"
	ocean_flag_extra="-meltfactor_pik ??"
	# This isn't implemented correctly yet
	;;
    "th")	
	echo "Ocean --> Ice coupling being used is |>> th <<|"
	ocean_flag=" -ocean th"
	extra_file=${indir}/ocean_th_file.nc
	ocean_flag_extra=" -ocean_th_file $extra_file"
	;;
    *)
	echo "ERROR: Ocean --> Ice coupler for $ocean unknown and not in the standard types described in PISM manual."
esac

# Ocean modifiers
scalar_sea_level_offset=0
if [[ $scalar_sea_level_offset == 1 ]]
then
    ocean_flag="${ocean_flag},delta_SL"
    # The data should be in meters!
    delta_SL_file="${indir}"/ocean_delta_SL_file.nc
    delta_SL_opts=" -ocean_delta_SL_file $delta_SL_file"
    ocean_modifier_opts="${ocean_modifier_opts} $delta_SL_opts"
fi

scalar_subshelf_temperature_offset=0
if [[ $scalar_subshelf_temperature_offset == 1 ]]
then
    ocean_flag="${ocean_flag},delta_T"
    # The data should be in meters!
    delta_T_file="${indir}"/ocean_delta_T_file.nc
    delta_T_opts=" -ocean_delta_T_file $delta_T_file"
    ocean_modifier_opts="${ocean_modifier_opts} $delta_T_opts"
fi

scalar_subshelf_mass_flux_offset=0
if [[ $scalar_subshelf_mass_flux_offset == 1 ]]
then
    ocean_flag="${ocean_flag},delta_SMB"
    # The data should be in meters!
    delta_SMB_file="${indir}"/ocean_delta_SMB_file.nc
    delta_SMB_opts=" -ocean_delta_SMB_file $delta_SMB_file"
    ocean_modifier_opts="${ocean_modifier_opts} $delta_SMB_opts"
fi

scalar_melange_back_pressure_fraction_offset=0
if [[ $scalar_melange_back_pressure_fraction_offset == 1 ]]
then
    ocean_flag="${ocean_flag},delta_MBP"
    # The data should be in meters!
    delta_MBP_file="${indir}"/ocean_delta_MBP_file.nc
    delta_MBP_opts=" -ocean_delta_MBP_file $delta_MBP_file"
    ocean_modifier_opts="${ocean_modifier_opts} $delta_MBP_opts"
fi

# Not yet implemented in the runscript:
# caching
   
ocean_command="${ocean_flag} ${ocean_flag_extra} ${ocean_modifier_opts}"

##############################
# Construct full coupler flag
##############################
coupler_opt="${bed_def_opt} ${atmo_command} ${surface_command} ${ocean_command}"


#####################################
#         ICE DYNAMIC OPTIONS
#####################################
hybrid_dynamics=1	# PG: Find out where this should go
##########
# CALVING
##########
# Calving Options (See page 68 of PISM manual)
calving=ocean_kill

# This will become a case statment later
if [[ $calving == "ocean_kill" ]]
then
    ocean_kill_file=$input_file_name
    calving_opt="$calving -ocean_kill_file $ocean_kill_file"
fi

# TODO: Find out if sia_e belongs to "calving" options?
sia_e=3.0			# This looks like a tuning factor;
                                # according to the manual it is
                                # "enhanced ice softness"

################
# STRESS BALANCE
################
# Shallow Sheet/Shelf Approximations
stress_balance=ssa+sia

# Plasticity Options
pseudo_plastic=1		        # 1 True, 0 False
pseudo_plastic_q=0.5		        # PG: Tuning Option?
till_effective_fraction_overburden=0.02 # PG: Tuning option?
tauc_slippery_grounding_lines=1		# 1 True, 0 False



################################################################################
# END OF USER INTERFACE
################################################################################

# The ex_file will contain only variables useful for coupling to
# GCM. The option o_size big (provided during the execution command)
# ensures that all the other variables are present in the main output
# files.

ts_file_name=${expid}_${icemod}_timeseries_${current_year}-${current_end}.nc
ex_file_name=${expid}_${icemod}_coupling_${current_year}-${current_end}.nc
ex_interval=10
# ex_vars=diffusivity,temppabase,tempicethk_basal,bmelt,tillwat,velsurfmag,mask,thk,topg,usurf
ex_vars=mask,thk,climatic_mass_balance_cumulative,discharge_flux_cumulative

output_file_name=${expid}_${icemod}_main_${current_year}-${current_end}.nc

# Prepare Work Directory
function prep_workdir {
    for f in ${workdir}/*
    do
	echo "Removing $f from ${workdir}..."
	rm -v $f
    done
    echo "Getting binary..."
    cp ${bindir}/${icemod} ${workdir}
    echo "Getting needed input files:"
    # TODO: Make "NEEDED FILES" variable
    cp ${indir}/${input_file_name} ${workdir}
}

# Prepare Input Directory
function prep_indir {
    # TODO: Make "NEEDED FILES" variable
    ## Copy files
    if [ ! -f ${indir}/${input_file_name} ]
    then
	cp ${pooldir}/input/${subpool}/${input_file_name} ${indir}
    fi    
}




# TODO: This still needs to be organized a bit. I am not sure if it
# makes sense to be here or somewhere else...

#Parse Options:
## Ice Dynamics Opts
### Calving
CALVING_OPTS="-calving $calving_opt -sia_e $sia_e"
ICE_DYN_OPTS="$ICE_DYN_OPTS $CALVING_OPTS"
### Stress Balance
# PG: Find out how to generalize this
# This is a standard value for topg_to_phi?
TTPHI="15.0,40.0,-300.0,700.0"
if [[ $pseudo_plastic -eq 1 ]]
then
    PSEUDOPLASTIC_OPT="-pseudo_plastic -pseudo_plastic_q $pseudo_plastic_q"
fi
TEFO_OPT="-till_effective_fraction_overburden $till_effective_fraction_overburden"
if [[ $tauc_slippery_grounding_lines -eq 1 ]]
then
    SGL="-tauc_slippery_grounding_lines"
fi
STRESS_BALANCE_OPTS="-stress_balance $stress_balance -topg_to_phi $TTPHI $PSEUDOPLASTIC_OPT $TEFO_OPT $SGL"
ICE_DYN_OPTS="$ICE_DYN_OPTS $STRESS_BALANCE_OPTS"
### Extra variable output for hybrid dynamics
if [[ "$hybrid_dynamics" -eq 1 ]]
then
    ex_vars="${ex_vars},hardav,velbase_mag,tauc"
fi



#########################################################
#             UNSORTED OPTIONS THAT NEED TO BE MOVED    
#########################################################



###################################
#     Launch the Model            
###################################
# Set check to 1 if you want to print out the pism execution command to check what would be done.

check=0

# Header for log:

echo "All options set for run with: "
echo "expid: $expid"

if [[ $check -eq 1 ]]
then
    echo prep_indir
    echo prep_workdir
    echo   $execution_command -n $numproc $icemod -i $input_file_name \
	   $bootstrap_opt \
	   $resolution_opt \
	   -ys $current_year -ye $current_end \
	   ${regrid_opt} \
	   ${coupler_opt} \
	   ${ICE_DYN_OPTS} \
	   -ts_file $ts_file_name -ts_times ${current_year}:yearly:${current_end} \
	   -extra_file $ex_file_name -extra_times ${current_year}:${ex_interval}:${current_end} -extra_vars $ex_vars \
	   -o $output_file_name -o_size big
else
    prep_indir
    prep_workdir
    cd ${workdir}
    $execution_command -n $numproc $icemod -i $input_file_name \
		       $bootstrap_opt \
		       $resolution_opt \
		       -ys $current_year -ye $current_end \
		       ${regrid_opt} \
		       ${coupler_opt} \
		       ${ICE_DYN_OPTS} \
		       -ts_file $ts_file_name -ts_times ${current_year}:yearly:${current_end} \
		       -extra_file $ex_file_name -extra_times ${current_year}:${ex_interval}:${current_end} -extra_vars $ex_vars \
		       -o $output_file_name -o_size big
fi
# Clean Up
mv $ts_file_name $ex_file_name $output_file_name $outdir
# Go back
cd ${scriptdir}

# Increase the run counter in the date file:
run_number=$(expr ${run_number} + 1)
echo ${run_number} > ${expid}.date

echo "Date file now is:"
cat ${expid}.date

echo "SSH EXECUTION OF NEXT RUN: ${run_number}"
module_command="module load pism_externals netcdf-tools slurm"

# This next line was tricky to actually figure out.
# Submit the next job:
ssh ollie0 bash -cl "' cd ${scriptdir}; pwd;  $module_command ; sbatch ${expid}.run '"


##################
#         END    
##################
echo "This PISM run finished on $(date)"
