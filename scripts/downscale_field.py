#!/usr/bin/env python
# coding: utf-8

import numpy as np
import time
import argparse
from scipy.io import netcdf
import matplotlib.pyplot as plt
import logging
import sys
from matplotlib.colors import Normalize
import warnings
from matplotlib.colors import from_levels_and_colors


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[32m'
    WARNING = '\033[33m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    
# Better plot:
class MidpointNormalize(Normalize):
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        # I'm ignoring masked values and all kinds of edge cases to make a
        # simple example...
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))


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

    
def parse_arguments():
    parser = argparse.ArgumentParser(description='Downscaling Script')
    parser.add_argument('ifile_lo', metavar="F lo", type=str,
                        help="The path of the input file to use (lo res)")
    parser.add_argument('ifile_hi', metavar="F hi", type=str,
                        help="The path of the input file to use (hi res)")
    parser.add_argument('-o', '--output', help="name of outfile netcdf file",
                        dest="ofilename",
                        default="ofile.nc")
    parser.add_argument('-d', '--debug', help="lots of output for debugging",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_const", dest="loglevel", const=logging.INFO)
    parser.add_argument("-p", "--plot", help="Plots the fields to check", 
                        action="store_true", dest="plot")
    return parser.parse_args()


def downscale_field(field_lo, elev_hi, elev_lo, mask, half_a_box=50):
    """
    Keyword Arguments:
    field_lo   -- the field you want to downscale at the low resolution, resampled to high resolution
    elev_hi    -- the elevation at the high resolution
    elev_lo    -- the elevation at the low resolution
    mask       -- the mask where the ice sheet area is found in the domain. <=0 will be excluded, >0 will be utilized.
    half_a_box -- (default 20)

    Paul J. Gierz, Wed Oct 19 10:11:01 2016
    """
    now = time.time()
    # Check dimensions:
    dims_field_lo = field_lo.squeeze().shape
    if len(dims_field_lo) > 3:
        logging.critical("You have more than 3 dimensions. I have no idea what to do")
        sys.exit("catastrophe! goodbye...")
    dims_elev_hi = elev_hi.squeeze().shape
    dims_elev_lo = elev_lo.squeeze().shape
    need_time = True
    if len(dims_elev_hi) != len(dims_elev_lo):
        logging.critical("The orography fields have different dimensions, you need to fix this!")
        logging.critical("High resolution is: " + str(dims_elev_hi))
        logging.critical("Lo resolution is: " + str(dims_elev_lo))
        sys.exit("catastrophe! goodbye...")
    if len(dims_field_lo) == len(dims_elev_hi):
        need_time = False
    elif (len(dims_field_lo) != len(dims_elev_hi)) and (dims_field_lo[1] == dims_elev_hi[0]):
        logging.warning("You probably have a time variable! I will try to loop over it")
    else:
        logging.critical("The field you are downscaling doesn't have the time dimension as the 1st dimension, this needs to be fixed!")
        sys.exit("catastrophe! goodbye...")    
    field_hi = np.empty(field_lo.shape) * np.nan
    half_a_box_y = round(0.8 * half_a_box)
    half_a_box_x = round(half_a_box)
    logging.warning("Half a box x and y are: (%s, %s)" % (half_a_box_x, half_a_box_y))
    LY, LX = np.shape(mask)
    logging.info("Shape will be %s,  %s" % (LY, LX))
    i_range = range(int(half_a_box_y), int(LY-half_a_box_y))
    j_range = range(int(half_a_box_x), int(LX-half_a_box_x))
    logging.debug("i_range is "+str(i_range))
    logging.debug("j_range is "+str(j_range))
    counter = 0
    if not need_time:
        for j in j_range:
            for i in i_range:
                logging.info("Working on index (%s, %s)" % (i, j))
                logging.debug("Mask value is: %s" % (mask[i, j]))
                if mask[i, j] > 0:
                    logging.debug("PASSED MASK SELECTION")
                    logging.debug("i slice is: %s to %s" % (i-half_a_box_y, i+half_a_box_y))
                    logging.debug("j slice is: %s to %s" % (j-half_a_box_x, j+half_a_box_x))
                    min_elev_lo = np.nanmin(
                        elev_lo[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])
                    max_elev_lo = np.nanmax(
                        elev_lo[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])

                    min_elev_hi = np.nanmin(
                        elev_hi[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])
                    max_elev_hi = np.nanmax(
                        elev_hi[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])

                    min_field_lo = np.nanmin(
                        field_lo[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])
                    max_field_lo = np.nanmax(
                        field_lo[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])

                    if j == (half_a_box_x):
                        bottom_k = -half_a_box_x
                        top_k = 0
                    elif j == (LX - half_a_box_x - 1):
                        bottom_k = 0
                        top_k = half_a_box_x
                    else:
                        bottom_k = 0
                        top_k = 0

                    if i == (half_a_box_y):
                        left_l = -half_a_box_y
                        right_l = 0
                    elif i == (LY - half_a_box_y - 1):
                        left_l = 0
                        right_l = half_a_box_y
                    else:
                        left_l = 0
                        right_l = 0
                else:
                    # Something about the mask didn't work
                    logging.debug("Mask not used at (%s, %s)" % (i, j))
                    left_l = 0
                    right_l = 0
                    top_k = 0
                    bottom_k = 0 

                for k in np.arange(bottom_k, top_k+1):
                    for l in np.arange(left_l, right_l+1):
                        if mask[i+l, j+k] > 0:
                            if (max_elev_lo == min_elev_lo):
                                field_hi[i+l, j+k] = field_lo[i+l, j+k]
                            else:
                                lapse_lo = (min_field_lo - max_field_lo)/(max_elev_lo - min_elev_lo)
                                field_hi[i+l, j+k] = lapse_lo * (elev_hi[i+l, j+k] - elev_lo[i+l, j+k]) + field_lo[i+l, j+k]
    else:
        for t in range(dims_field_lo[0]):
            logging.debug("WORKING ON TIMESTEP %s" % t)
            for j in j_range:
                for i in i_range:
                    logging.info("Working on index (%s, %s)" % (i, j))
                    logging.debug("Mask value is: %s" % (mask[i, j]))
                    if mask[i, j] > 0:
                        logging.debug("PASSED MASK SELECTION")
                        logging.debug("i slice is: %s to %s" % (i-half_a_box_y, i+half_a_box_y))
                        logging.debug("j slice is: %s to %s" % (j-half_a_box_x, j+half_a_box_x))
                        min_elev_lo = np.nanmin(
                            elev_lo[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])
                        max_elev_lo = np.nanmax(
                            elev_lo[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])

                        min_elev_hi = np.nanmin(
                            elev_hi[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])
                        max_elev_hi = np.nanmax(
                            elev_hi[i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])

                        min_field_lo = np.nanmin(
                            field_lo[t, i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])
                        max_field_lo = np.nanmax(
                            field_lo[t, i-half_a_box_y:i+half_a_box_y, j-half_a_box_x:j+half_a_box_x])

                        if j == (half_a_box_x):
                            bottom_k = -half_a_box_x
                            top_k = 0
                        elif j == (LX - half_a_box_x - 1):
                            bottom_k = 0
                            top_k = half_a_box_x
                        else:
                            bottom_k = 0
                            top_k = 0

                        if i == (half_a_box_y):
                            left_l = -half_a_box_y
                            right_l = 0
                        elif i == (LY - half_a_box_y - 1):
                            left_l = 0
                            right_l = half_a_box_y
                        else:
                            left_l = 0
                            right_l = 0
                    else:
                        # Something about the mask didn't work
                        logging.debug("Mask not used at (%s, %s)" % (i, j))
                        left_l = 0
                        right_l = 0
                        top_k = 0
                        bottom_k = 0 

                    for k in np.arange(bottom_k, top_k+1):
                        for l in np.arange(left_l, right_l+1):
                            if mask[i+l, j+k] > 0:
                                if (max_elev_lo == min_elev_lo):
                                    field_hi[t, i+l, j+k] = field_lo[t, i+l, j+k]
                                else:
                                    lapse_lo = (min_field_lo - max_field_lo)/(max_elev_lo - min_elev_lo)
                                    field_hi[t, i+l, j+k] = lapse_lo * (elev_hi[i+l, j+k] - elev_lo[i+l, j+k]) + field_lo[t, i+l, j+k]
    if (counter > 0):
        logging.warning("Neither condition was used %s times" % counter)
    logging.info("Finished! Time was %s" % str(time.time()-now))
    return field_hi


def main():
    args = parse_arguments()
    fmt = MyFormatter()
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(args.loglevel)

    T_lo_varname = "TT"
    H_lo_varname = "SH"
    H_hi_varname = "SH"
    mask_varname = "MSK"

    # Make the output file:
    shutil.copy(args.ifile_lo, args.ofilename)

    T_lo = netcdf.netcdf_file(args.ifile_lo).variables[T_lo_varname].data[6, -1, :, :].squeeze()
    T_or = netcdf.netcdf_file(args.ifile_hi).variables[T_lo_varname].data[6, -1, :, :].squeeze()
    H_lo = netcdf.netcdf_file(args.ifile_lo).variables[H_lo_varname].data.squeeze()

    H_hi = netcdf.netcdf_file(args.ifile_hi).variables[H_hi_varname].data.squeeze()
    mask = netcdf.netcdf_file(args.ifile_hi).variables[mask_varname].data.squeeze()
    T_hi = downscale_field(T_lo, H_hi, H_lo, mask, half_a_box=20)

    # TODO: Write ofile to netcdf
    
    if args.plot:
        num_levels = 20
        vmin, vmax = -45, 25
        midpoint = 0
        levels = np.linspace(vmin, vmax, num_levels)
        midp = np.mean(np.c_[levels[:-1], levels[1:]], axis=1)
        vals = np.interp(midp, [vmin, midpoint, vmax], [0, 0.5, 1])
        colors = plt.cm.seismic(vals)
        cmap, norm = from_levels_and_colors(levels, colors)
        norm = MidpointNormalize(midpoint=0)

        plt.figure("Temperatures (lo, hi) and Mask")
        ax1 = plt.subplot(131)
        m = ax1.contourf(T_lo, interpolation='none', extend="both", cmap=cmap, norm=norm)

        ax2 = plt.subplot(132)
        m = ax2.contourf(T_hi, interpolation='none', extend="both", cmap=cmap, norm=norm)

        ax3 = plt.subplot(133)
        m = ax3.contourf(T_or, interpolation='none', extend="both", cmap=cmap, norm=norm)

        plt.show()

if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
