#!/usr/bin/env python
# coding: utf-8

#################
# IMPORT MODULES
#################

import argparse
import datetime
import logging
from scipy.io import netcdf
import os
import shutil
import sys
import warnings


try:
    from downscale_field import downscale_field
    downscale_available = True
except ImportError:
    print "downscale_field.py not found, downscaling will be disabled"
    downscale_available = False
try:
    import cdo
except ImportError:
    raise ImportError(
        "cdo-python interface could not be found. " +
        "Try installing it via: \n pip install --user cdo")
try:
    import nco
except ImportError:
    raise ImportError(
        "nco-python interface could not be found. " +
        "Try installing it via: \n pip install --user nco")

###############
# LOGGER STUFF
###############


# Colors for logger
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[32m'
    WARNING = '\033[33m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Custom formatter
class MyFormatter(logging.Formatter):

    err_fmt = bcolors.FAIL + "ERROR: %(msg)s" + bcolors.ENDC
    dbg_fmt = bcolors.WARNING + \
        "DBG: %(module)s: %(lineno)d: %(msg)s" + bcolors.ENDC
    info_fmt = bcolors.OKGREEN + "INFO: %(msg)s" + bcolors.ENDC
    warn_fmt = bcolors.FAIL + "WARNING: %(msg)s" + bcolors.ENDC

    def __init__(self, fmt="%(levelno)s: %(msg)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = MyFormatter.dbg_fmt

        elif record.levelno == logging.INFO:
            self._fmt = MyFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._fmt = MyFormatter.err_fmt

        elif record.levelno == logging.WARN:
            self._fmt = MyFormatter.warn_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result

#########
# PARSER
#########


def _parse_file_and_var(s):
    try:
        f, v = map(str, s.split(','))
        return f, v
    except:
        raise argparse.ArgumentTypeError("Must be given as: filename, varname")


def parse_arguments():
    """
    This function looks scary. It just gets command line arguments

    Paul J. Gierz, Tue Oct 11 13:12:43 2016
    """
    ##########################################################################
    parser = argparse.ArgumentParser(description='Generates ISM inputs from GCM output. Designed for PISM, but could possibly serve other purposes as well.',
                                     epilog="Version: 0.1.0 \n Paul J. Gierz, AWI Bremerhaven")
    parser.add_argument("-o", "--ofile", help="The filename of the output file, " +
                        "defaults to ofile.nc",
                        default="ofile.nc")
    parser.add_argument('--debug', help="lots of output for debugging",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_const", dest="loglevel", const=logging.INFO)
    subparsers = parser.add_subparsers(dest="command")
    ##########################################################################
    remap_parser_group = subparsers.add_parser("remap",
                                               help="Options that need to be provided for the 1st order conservative remapping to a ISM grid via cdo remapcon")
    remap_parser_group.add_argument('-igcm', '--ifile_gcm',
                                    required=True,
                                    help="The \"input\" file to use from the GCM")
    remap_parser_group.add_argument('-igrid', '--ifile_griddes',
                                    required=True,
                                    help="The grid description you want to use, either built into CDO directly, or from a griddes file")
    ##########################################################################
    interpolate_parser_group = subparsers.add_parser("interpolate",
                                                     help="Interpolates a field via cdo remapbil, works similarly to remap command")
    interpolate_parser_group.add_argument('-igcm', '--ifile_gcm',
                                          required=True,
                                          help="The \"input\" file to use from the GCM")
    interpolate_parser_group.add_argument('-igrid', '--ifile_griddes',
                                          required=True,
                                          help="The grid description you want to use, either built into CDO directly, or from a griddes file")
    ##########################################################################
    downscale_parser_group = subparsers.add_parser("downscale",
                                                   help="Options that need to be provided for downscaling of GCM outputs to fine grids")
    downscale_parser_group.add_argument("-dgcm", "--downscale_gcm",
                                        type=_parse_file_and_var,
                                        help="Downscale (file,variable) with low resolution (target) field")
    downscale_parser_group.add_argument("-dhires", "--downscale_hires",
                                        type=_parse_file_and_var,
                                        help="Downscale (file,variable) with high resolution (target) orography")
    downscale_parser_group.add_argument("-dlores", "--downscale_lores",
                                        type=_parse_file_and_var,
                                        help="Downscale (file,variable) with low resolution (original) orography")
    downscale_parser_group.add_argument("-dmask", "--downscale_mask",
                                        type=_parse_file_and_var,
                                        help="Downscale mask (file,variable)")
    ##########################################################################
    ##########################################################################
    # TODO: Find out which of these is not needed
    ##########################################################################
    atmosphere_top = subparsers.add_parser("prep_file_atmo",
                                           help="Prepares GCM netcdf files to work in PISM")
    atmosphere_top.add_argument("pism_ifile", help="The pism input file this atmosphere forcing will be used with")
    atmosphere_group = atmosphere_top.add_subparsers(dest="atmo_command")
    ##############################
    atmosphere_yearly_cycle_group = atmosphere_group.add_parser("yearly_cycle",
                                                                help="Make files for pism \"yearly_cycle\" atmosphere coupling")
    atmosphere_yearly_cycle_group.add_argument("-itemp", "--ifile_temperature",
                                               required=True,
                                               help="The file containing a yearly cycle of temperature, already on PISM grid")
    atmosphere_yearly_cycle_group.add_argument("-iprecip", "--ifile_precipitation",
                                               required=True,
                                               help="The file containing a yearly cycle of precipitation on PISM grid")
    ##############################
    atmosphere_given_group = atmosphere_group.add_parser("given",
                                                         help="Make files for pism \"given\" atmosphere coupling")
    atmosphere_given_group.add_argument("-itemp", "--ifile_temperature",
                                        required=True,
                                        help="The file containing a yearly cycle of temperature, already on PISM grid")
    atmosphere_given_group.add_argument("-iprecip", "--ifile_precipitation",
                                        required=True,
                                        help="The file containing a yearly cycle of precipitation on PISM grid")
    ##############################
    atmosphere_searise_greenland_group = atmosphere_group.add_parser("searise_greenland",
                                                                     help="Make files for pism \"searise_greenland\" atmosphere coupling")
    ##############################
    atmosphere_one_station_group = atmosphere_group.add_parser("one_station",
                                                               help="Make files for pism \"one_station\" atmosphere coupling")
    ##########################################################################
    ##########################################################################
    ##########################################################################
    return parser.parse_args()


##########
# CLASSES
##########

class pism_output_file(object):
    # Something something
    pass


############
# FUNCTIONS
############
def remap(args):
    CDO = cdo.Cdo()
    if not os.path.exists(args.ofile):
        CDO.remapcon(args.ifile_griddes, input=args.ifile_gcm,
                     output=args.ofile, options="-f nc -v")
        logging.info("Outfile generated here: %s" % (args.ofile))
    else:
        logging.info("Outfile exists here: %s" % (args.ofile))


def interpolate(args):
    CDO = cdo.Cdo()
    if not os.path.exists(args.ofile):
        CDO.remapbil(args.ifile_griddes, input=args.ifile_gcm,
                     output=args.ofile, options="-f nc -v")
        logging.info("Outfile generated here: %s" % (args.ofile))
    else:
        logging.info("Outfile exists here: %s" % (args.ofile))


def given_atmo(args):
    fin_temp = netcdf.netcdf_file(args.ifile_temperature)
    if fin_temp.source == "ECHAM5.4":
        tempvarname = "temp2"
    elif fin_temp.source == "ECHAM6":
        tempvarname = "temp2"
    else:
        logging.warn("Model unknown, waiting for user response...")
        print fin_temp.variables
        tempvarname = input("What is the temperature varname you want to use? ")
    fin_precip = netcdf.netcdf_file(args.ifile_precipitation)
    if fin_precip.source == "ECHAM5.4":
        precipvarname = "precip"
    elif fin_precip.source == "ECHAM6":
        precipvarname = "precip"
    else:
        logging.warn("Model unknown, waiting for user response...")
        print fin_precip.variables
        precipvarname = input("What is the precip varname you want to use? ")
    shutil.copy(fin_temp.filename, args.ofile)
    fout = netcdf.netcdf_file(args.ofile, "a")
    ############################################################
    # Write Air Temperature
    ############################################################
    air_temp = fout.createVariable("air_temp", float, ("time", 'y', 'x'))
    air_temp.standard_name = "air_temperature"
    air_temp.units = "K"
    air_temp.long_name = "Air Temperature (2 meter)"
    air_temp.grid_mapping = "mapping"
    air_temp.coordinates = "lon lat"
    air_temp[:] = fin_temp.variables[tempvarname].data
    ############################################################
    # Write Precipitation
    ############################################################
    precip = fout.createVariable("precipitation", float, ("time", 'y', 'x'))
    precip.units = "m s-1"
    precip.long_name = "Yearly mean total precipitation"
    precip.standard_name = "lwe_precipitation_rate"
    precip._FillValue = "-9.e+33f"
    p = fin_precip.variables[precipvarname].data
    p = p/910.
    precip[:] = p
    ############################################################
    # Write output
    ############################################################
    fout.author = "Paul J. Gierz"
    fout.institution = "Alfred Wegener Institute"
    fout.history = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+" Modified with script:\n pism_input_from_gcm.py prep_file_atmo "+fin_temp.filename+" "+fin_precip.filename+"\n"+fout.history
    fout.sync()
    ############################################################
    # Make X and Y
    ############################################################
    logging.warn("Trying to do NCO by python-nco interface...")
    NCO = nco.Nco()
    NCO.ncks(options="-c", input=args.pism_ifile, output="foo.nc")
    NCO.ncrename(options="-d x1,x -d y1,y -v x1,x -v y1,y", input="foo.nc", output="foo1.nc")
    # inputfiles = " ".join([temp_ofile, fout.filename])
    # PG: Dirty hack, somehow the NCO.ncks doesn't work, so we do over os instead
    os.system("ncks -q -A foo1.nc "+fout.filename)
    os.system("rm foo.nc foo1.nc")
    logging.warn("The warning just produced by ncks at this point does not cause any problems")
    ############################################################
    return None


def yearly_cycle_atmo(args):
    fin_temp = netcdf.netcdf_file(args.ifile_temperature)
    if fin_temp.source == "ECHAM5.4":
        tempvarname = "temp2"
    elif fin_temp.source == "ECHAM6":
        tempvarname = "temp2"
    else:
        logging.warn("Model unknown, waiting for user response...")
        print fin_temp.variables
        tempvarname = input("What is the temperature varname you want to use? ")
    fin_precip = netcdf.netcdf_file(args.ifile_precipitation)
    if fin_precip.source == "ECHAM5.4":
        precipvarname = "precip"
    elif fin_precip.source == "ECHAM6":
        precipvarname = "precip"
    else:
        logging.warn("Model unknown, waiting for user response...")
        print fin_precip.variables
        precipvarname = input("What is the precip varname you want to use? ")
    shutil.copy(fin_temp.filename, args.ofile)
    fout = netcdf.netcdf_file(args.ofile, "a")
    ############################################################
    # Make Annual Surface Temp
    ############################################################
    air_temp_mean_annual = fout.createVariable("air_temp_mean_annual", float,
                                               ('y', 'x'))
    air_temp_mean_annual.standard_name = "air_temperature"
    air_temp_mean_annual.units = "K"
    air_temp_mean_annual.long_name = "Annual Mean Air Temperature (2 meter)"
    air_temp_mean_annual.grid_mapping = "mapping"
    air_temp_mean_annual.coordinates = "lon lat"
    air_temp_mean_annual._FillValue = "-9.e+33f"
    air_temp_mean_annual[:] = fin_temp.variables[tempvarname].data.mean(axis=0)

    ############################################################
    # July Mean Surface Temp
    ############################################################
    air_temp_mean_july = fout.createVariable("air_temp_mean_july", float,
                                             ('y', 'x'))
    air_temp_mean_july.standard_name = "air_temperature"
    air_temp_mean_july.units = "K"
    air_temp_mean_july.long_name = "July Mean Air Temperature (2 meter)"
    air_temp_mean_july.grid_mapping = "mapping"
    air_temp_mean_july.coordinates = "lon lat"
    air_temp_mean_july._FillValue = "-9.e+33f"
    air_temp_mean_july[:] = fin_temp.variables[tempvarname].data[6, :, :]
    ############################################################
    # Precipitation
    ############################################################
    precipitation = fout.createVariable("precipitation", float,
                                        ('y', 'x'))
    precipitation.units = "m s-1"
    precipitation.long_name = "Yearly mean total precipitation"
    precipitation.standard_name = "lwe_precipitation_rate"
    precipitation._FillValue = "-9.e+33f"
    p = fin_precip.variables[precipvarname].data.mean(axis=0)
    # PG: This is yearly average, maybe better to use a full cycle
    p = p/910.  # PG: Convert from kg/m^2s => m/s ice equivalent, see NOTE
    precipitation[:] = p
    ############################################################
    # NOTE: Someone needs to confirm this
    # p [kg/m^-2 * s] = [1 l/s] = [1 mm/s] * rho_liquid / rho_solid * 1 [m] / 1000 [mm] = p [m_ice/s]
    ############################################################
    # Save the output and add some info
    #
    # PG: File needs to be saved first, otherwise none of the new data
    # will be written to it.
    #
    ############################################################
    fout.author = "Paul J. Gierz"
    fout.institution = "Alfred Wegener Institute"
    fout.history = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")+" Modified with script:\n pism_input_from_gcm.py prep_file_atmo "+fin_temp.filename+" "+fin_precip.filename+"\n"+fout.history
    fout.sync()
    ############################################################
    # Make X and Y
    ############################################################
    # TODO: This still needs to be done in some clever-ish way
    # For now, tell the user to do it by hand:
    # logging.warn("The X and Y coordinates are not defined in this gcm_outputfile.")
    # logging.warn("They need to be added by copying from the PISM input file:")
    # logging.warn("ncks -c ${pism_inputfile} foo.nc")
    # logging.warn("ncks -A foo.nc ${gcm_outputfile}")
    logging.warn("Trying to do NCO by python-nco interface...")
    # PG: The NCO part has not yet been tested
    NCO = nco.Nco()
    NCO.ncks(options="-c", input=args.pism_ifile, output="foo.nc")
    NCO.ncrename(options="-d x1,x -d y1,y -v x1,x -v y1,y", input="foo.nc", output="foo1.nc")
    # inputfiles = " ".join([temp_ofile, fout.filename])
    # PG: Dirty hack, somehow the NCO.ncks doesn't work, so we do over os instead
    os.system("ncks -q -A foo1.nc "+fout.filename)
    os.system("rm foo.nc foo1.nc")
    logging.warn("The warning just produced by ncks at this point does not cause any problems")
    ############################################################
    return None


def downscale(args):
    if downscale_available:
        field_hi = downscale_field(
            netcdf.netcdf_file(args.downscale_gcm[0]).variables[args.downscale_gcm[1]].data.squeeze(),
            netcdf.netcdf_file(args.downscale_hires[0]).variables[args.downscale_hires[1]].data.squeeze(),
            netcdf.netcdf_file(args.downscale_lores[0]).variables[args.downscale_lores[1]].data.squeeze(),
            netcdf.netcdf_file(args.downscale_mask[0]).variables[args.downscale_mask[1]].data.squeeze()
        )
        fout = netcdf.netcdf_file(args.ofile, "a")
        downscaled_temp = fout.createVariable("air_temp_downscaled", float,
                                              ("y", "x"))

        downscaled_temp[:] = field_hi
    else:
        logging.error("Downscaling not available!")


#############
# MAIN STUFF
#############
# The main function is actually deceptively small
def main():
    args = parse_arguments()
    not_impl_str = "not implemented, exiting! \n (Paul thought it wasn't useful...)"
    fmt = MyFormatter()
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(args.loglevel)
    if args.command == "remap":
        remap(args)
    if args.command == "interpolate":
        interpolate(args)
    if args.command == "prep_file_atmo":
        if args.atmo_command == "given":
            given_atmo(args)
        if args.atmo_command == "yearly_cycle":
            yearly_cycle_atmo(args)
        if args.atmo_command == "searise_greenland":
            logging.critical("%s  %s  :" + not_impl_str) % (args.command, args.atmo_command)
            sys.exit(42)        # Because 42 is the answer
        if args.atmo_command == "one_station":
            logging.critical("%s  %s  :" + not_impl_str) % (args.command, args.atmo_command)
            sys.exit(42)
    if args.command == "downscale":
        downscale(args)

if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()


#################
# END OF PROGRAM
#################

# Paul J. Gierz, AWI Bremerhaven
