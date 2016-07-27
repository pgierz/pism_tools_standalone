#!/bin/bash
################################################################################
# BATCH HEADERS
################################################################################
#SBATCH --job-name=PISM_Test
#SBATCH -p mpp
#SBATCH --ntasks=144
#SBATCH --time=1:00:00
################################################################################

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
# -----------------------------------------------------------------------------#
# AWI Bremerhaven                                                              #
################################################################################

################################################################################
# TODOs                                                                        
#
# * DONE SBATCH headers?
# * TODO Script headings and sections
# * TODO organize script in such a way that it makes sense
# * TODO separate parsing of options from setting of options. The user
#        doesn't need to see everything
#
################################################################################

icemod=pismr

#############################################
#                     RESOLUTION OPTIONS    
#############################################


res=low				# Pick between: low (20km), med (10km), high (5km)

if [[ $res == "low" ]]
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
    echo "$0 Error: High resolution not set yet!"
    exit 42
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

resolution_opt="-Mx $xres_ice -My $yres_ice -Mz $zres_ice -Mbz $bz -z_spacing $z_spacing_opt -Lz $Lz -Lbz $Lbz -skip -skip_max $skip_max"



#########################################################
# RESTART (Regrid?? why the fuck is this called regrid?)
#########################################################
regrid=0			# True 1; False 0
if [[ $regrid -eq 1 ]]
then
    regrid_file=PLACEHOLDER	# PG: file to regrid from goes here
    regrid_vars=litho_temp,thk,enthalpy,tillwat,bmelt # PG: Copied from example
fi
regrid_opt="-regrid_file $regrid_file -regrid_vars $regrid_vars"

######################
# Bedrock Deformation
######################

# Which bedrock deformation model to use.
# Allowed values: none, iso, lc
bed_def=none
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


###############################################################
#                     COUPLING OPTIONS                        
###############################################################

###############################
# Atmosphere >--|> Ice Forcings
###############################
atmophere=none
case $atmosphere in
    "none")
	echo "No atmosphere coupling is used!"
	atmo_opts=""
	;;
    "given")
	echo "Atmosphere -> Ice coupling type being used: |>>> given <<<|"
	atmo_flag=" -atmosphere given"
	extra_file=${indir}/atmo_given_file.nc
	atmo_flag_extra=" -atmosphere_given_file $extra_file"
	;;
    "yearly_cycle")
	echo "Atmosphere -> Ice coupling type being used: |>>> yearly_cycle <<<|"
	echo "Atmosphere coupler for this type not implemented, please go whack Paul over the head to fix this..."
	;;
    "searise_greenland")
	echo "Atmosphere -> Ice coupling type being used: |>>> searise_greenland <<<|"
	atmo_flag=" -atmosphere searise_greenland"
	extra_file=${indir}/atmo_searise_greenland_file.nc
	atmo_flag_extra=" -atmosphere=searise_greenland_file $extra_file"
	echo "Atmosphere coupler for this type not implemented, please go whack Paul over the head to fix this..."
	;;
    "one_station")
	echo "Atmosphere -> Ice coupling type being used: |>>> one_station <<<|"
	echo "Atmosphere coupler for this type not implemented, please go whack Paul over the head to fix this..."
	;;
    *)
	echo "Atmosphere coupler for $atmosphere unknown and not in standard types described in PISM manual. Go talk to Paul, he will figure it out..."
esac

# atmosphere_modifiers
scalar_temperature_offsets=1	# True 1; False 0
if [[ $scalar_temperature_offsets == 1 ]]
then
    atmo_flag="${atmo_flag},delta_T"
    # The file needs to be in Kelvin!
    atmosphere_delta_T_file=${indir}/atmo_delta_T_file.nc
    scalar_temperature_offsets_opts=" -atmosphere_delta_T_file $atmosphere_delta_T_file"
    atmo_modifer_opts="$atmo_modifer_opts $scalar_temperature_offsets_opts"
fi

scalar_precipitation_offsets=1	# True 1; False 0
if [[ $scalar_temperature_offsets == 1 ]]
then
    atmo_flag="${atmo_flag},delta_P"
    atmosphere_delta_P_file=${indir}/atmo_delta_P_file.nc
    scalar_temperature_offsets_opts=" -atmosphere_delta_P_file $atmosphere_delta_P_file"
    atmo_modifer_opts="$atmo_modifer_opts $scalar_temperature_offsets_opts"
fi

paleo_precipitation=1 		# True 1; False 0
if [[ $paleo_precipitation == 1 ]]
then
    atmo_flag="${atmo_flag},paleo_precip"
    extra_file=${indir}/paleo_precip_file.nc
    paleo_precip_opts=" -atmosphere_paleo_precip"    
fi

# The following atmospheric modifers are not (yet) implemented in the
# run script logic, but can be set with command switches at the end if
# the command string is modified at the end of the runscript.

# scalar_precipitation_scaling
# lapse_rate
# anomaly

#########################
# Surface Process Models
#########################

surface_opt="given"
case $surface_opt in
    "simple")
	surface_opts=" -surface simple"
	;;
    "given")
	surface_given_file=${input_file_name}
	surface_opts=" -surface given -surface_given_file $surface_given_file"
	;;
    "elevation")
	echo "surface type for $surface_opt not implemented, please go whack Paul over the head to fix this..."
	;;
    "pdd")
	# Fuck this one is complicated...
	pdd_sd_file=pdd_sd_file.nc
	
	surface_opts=" -surface pdd "
	;;
    "pik")

	echo "surface type for $surface_opt not implemented, please go whack Paul over the head to fix this..."
	;;
    *)
	echo "unknown surface opt provided. Go talk to Paul, he will figure it out..."
esac


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

# Header for log:

echo "This PISM run was perfomed on $HOSTNAME on $(date)"
echo "expid: $expid"


# Directories
outdir=${homedir}/${expid}/output
workdir=${homedir}/${expid}/work
indir=${homedir}/${expid}/input


ts_file_name=${expid}_${icemod}_timeseries_${start_year}-${end_year}.nc
ex_file_name=${expid}_${icemod}_extra_${start_year}-${end_year}.nc
ex_interval=100
ex_vars=diffusivity,temppabase,tempicethk_basal,bmelt,tillwat,velsurfmag,mask,thk,topg,usurf

output_file_name=${expid}_${icemod}_main_${start_year}-${end_year}.nc

# Prepare Work Directory
## Empty work
for f in ${workdir}/*
do
echo "Removing $f from ${workdir}..."
rm -v $f
done

## Copy files
if [ ! -f ${indir}/${input_file_name} ]
then
    cp ${pooldir}/input/${subpool}/${input_file_name} ${indir}
fi

cp ${indir}/${input_file_name} ${workdir}
cp ${bindir}/${icemod} ${workdir}

# Parse Options:
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

########################################
# DIRECTORY STRUCTURES
########################################

expid=@EXPID@
homedir=/work/ollie/pgierz/pism_standalone/
bindir=/work/ollie/pgierz/pism0.7/bin/
pooldir=/work/ollie/pgierz/pool_pism/
subpool=examples_greenland

numproc=4			# Number of processors to use
execution_command="srun --mpi=pmi2"

# Input File Name:
input_file_name=pism_Greenland_5km_v1.1.nc

# Bootstrapping?
bootstrap=1
if [[ $bootstrap -eq 1 ]]
then
    bootstrap_opt="-bootstrap"
fi

# Time Control
start_year=-10000
end_year=0

#########
# FORCING
#########

surface="given -surface_given_file $input_file_name"



###################################
#     Launch the Model            
###################################

cd ${workdir}
$execution_command -n $numproc $icemod -i $input_file_name \
		   $bootstrap_opt \
		   $resolution_opt \
		   -ys $start_year -ye $end_year \
		   -surface $surface \
		   -${ICE_DYN_OPTS} \
		   -ts_file $ts_file_name -ts_times ${start_year}:yearly:${end_year} \
		   -extra_file $ex_file_name -extra_times ${start_year}:${ex_interval}:${end_year} -extra_vars $ex_vars \
		   -o $output_file_name
# Clean Up
mv $ts_file_name $ex_file_name $output_file_name $outdir

# Go back
cd -

##################
#         END    
##################    
echo "This PISM run finished on $(date)"




