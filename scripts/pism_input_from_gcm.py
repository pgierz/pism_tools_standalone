#!/usr/bin/env python
# coding: utf-8

import argparse
import logging
from scipy.io import netcdf
import os
import sys
import warnings


try:
    from downscale_field import downscale_field
    downscale_available=True
except ImportError:
    print "downscale_field.py not found, downscaling will be disabled"
    downscale_available=False
try:
    import cdo
except ImportError:
    raise ImportError("cdo-python interface could not be found. Try installing it via: \n pip install --user cdo")

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

    err_fmt = bcolors.FAIL+"ERROR: %(msg)s"+bcolors.ENDC
    dbg_fmt = bcolors.WARNING+"DBG: %(module)s: %(lineno)d: %(msg)s"+bcolors.ENDC
    info_fmt = bcolors.OKGREEN+"INFO: %(msg)s"+bcolors.ENDC
    warn_fmt = bcolors.FAIL+"FAILURE: %(msg)s"+bcolors.ENDC

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

    
def _parse_file_and_var(s):
    try:
        f, v = map(str, s.split(','))
        return f, v
    except:
        raise argparse.ArgumentTypeError("Must be given as: filename, varname")

    
def parse_arguments():
    ################################################################################
    parser = argparse.ArgumentParser(description='Generates ISM inputs from GCM output. Designed for PISM, but could possibly serve other purposes as well.',
                                     epilog="Paul J. Gierz, AWI Bremerhaven")
    parser.add_argument("-o", "--ofile", help="The filename of the output file, defaults to ofile.nc",
                        default="ofile.nc")
    parser.add_argument('--debug', help="lots of output for debugging",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_const", dest="loglevel", const=logging.INFO)
    ################################################################################
    interpolation_parser_group = parser.add_argument_group("Remapping",
                                                           "Options that need to be provided for the 1st order conservative remapping to a ISM grid via cdo remapcon")
    interpolation_parser_group.add_argument('-igcm', '--ifile_gcm',
                                            type=_parse_file_and_var,
                                            help="The \"input\" (file,variable) to use from the GCM")
    interpolation_parser_group.add_argument('-igrid', '--ifile_griddes',
                                            help="The grid description you want to use, either built into CDO directly, or from a griddes file")
    ################################################################################
    downscale_parser_group = parser.add_argument_group("Downscaling",
                                                       "Options that need to be provided for downscaling of GCM outputs to fine grids")
    downscale_parser_group.add_argument("-dhires", "--downscale_hires",
                                        type=_parse_file_and_var, 
                                        help="Downscale (file,variable) with high resolution (target) orography")
    downscale_parser_group.add_argument("-dlores", "--downscale_lores",
                                        type=_parse_file_and_var, 
                                        help="Downscale (file,variable) with low resolution (original) orography")
    downscale_parser_group.add_argument("-dmask", "--downscale_mask",
                                        type=_parse_file_and_var, 
                                        help="Downscale mask (file,variable)")
    ################################################################################
    return parser.parse_args()

        
def main():
    args = parse_arguments()
    print args
    fmt = MyFormatter()
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(args.loglevel)

    CDO = cdo.Cdo()
    if not os.path.exists(args.ofile):
        CDO.remapcon(args.ifile_griddes, input=args.ifile_gcm[0], output=args.ofile, options="-f nc -v")
        logging.info("Outfile generated here: %s" % (args.ofile))
    else:        
        logging.info("Outfile exists here: %s" % (args.ofile))
    if downscale_available:
        field_hi = downscale_field(
            netcdf.netcdf_file(args.ofile).variables[args.ifile_gcm[1]].data.squeeze(),
            netcdf.netcdf_file(args.downscale_hires[0]).variables[args.downscale_hires[1]].data.squeeze(),
            netcdf.netcdf_file(args.downscale_lores[0]).variables[args.downscale_lores[1]].data.squeeze(),
            netcdf.netcdf_file(args.downscale_mask[0]).variables[args.downscale_mask[1]].data.squeeze()
            )
    else:
        logging.error("Downscaling not available!")
    
if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
