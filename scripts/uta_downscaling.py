#!/usr/bin/env python
# coding: utf-8

import numpy as np
import time
import argparse
from scipy.io import netcdf
import matplotlib.pyplot as plt
import logging
import sys


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[33m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    
# Custom formatter
class MyFormatter(logging.Formatter):

    err_fmt = bcolors.FAIL+"ERROR: %(msg)s"+bcolors.ENDC
    dbg_fmt = bcolors.WARNING+"DBG: %(module)s: %(lineno)d: %(msg)s"+bcolors.ENDC
    info_fmt = bcolors.HEADER+"%(msg)s"+bcolors.ENDC

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
    parser.add_argument('-d', '--debug', help="lots of output for debugging",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_const", dest="loglevel", const=logging.INFO)
    return parser.parse_args()


def downscale_field(field_lo, elev_hi, elev_lo, mask, half_a_box=20):
    """
    Downscaling routine based upon MATLAB function written by Uta Krebs-Kanzow

    Paul J. Gierz, Fri Sep 16 10:25:20 2016

    Keyword Arguments:
    field_lo   -- input temperature from coarse grid (should already be resampled)
    elev_hi    -- orographic information of the high resolution grid
    elev_lo    -- orographic information of the low resolution grid; resampled to the high resolution grid
                  Assuming hi-res is 9x better resolved: If on lo-res (x1, y1) = 50, (x2, y1) = 75, then on hi-res
                  (x1, y1) = 50, (x2, y1) = 50, (x3, y1) = 50, (x4, y1)=75, (x5, y1) = 75, (x6, y1) = 75
    mask       -- Mask of ice sheet domain to use (hi res!!)
    half_a_box -- how many hires gridboxes we need to get into the next lores regridbox
    
    return field_hi
    """
    now = time.time()

    field_hi = np.empty(field_lo.shape) * np.nan
    logging.debug("PG: type of field_hi is"+str(type(field_hi)))
    factor = 0.8                # PG: compensates for different x and y resolutions
    half_a_box_x = round(factor * half_a_box)
    half_a_box_y = round(half_a_box)

    logging.debug("half_a_box_x is "+str(half_a_box_x))
    logging.debug("half_a_box_y is "+str(half_a_box_y))

    size_x, size_y = field_lo.shape

    logging.debug("size_x is "+str(size_x))
    logging.debug("size_y is "+str(size_y))

    logging.info("Downscaling Temperature")
    logging.info("Start...")
    logging.debug("PG: j range will be "+str(half_a_box_y)+" "+str(size_y - half_a_box_y))
    logging.debug("PG: i range will be "+str(half_a_box_x)+" "+str(size_x - half_a_box_x))
    for j in range(int(half_a_box_y), int(size_y - half_a_box_y)):
        for i in range(int(half_a_box_x), int(size_x - half_a_box_x)):
    # for j in range(size_y):
    #     for i in range(size_x):
            if mask[i, j] > 0:
            # if True:
                min_height_lo = np.nanmin(
                    elev_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                max_height_lo = np.nanmax(
                    elev_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                min_height_hi = np.nanmin(
                    elev_hi[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                max_height_hi = np.nanmax(
                    elev_hi[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                min_value = np.nanmin(
                    field_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                max_value = np.nanmax(
                    field_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                if j == (half_a_box_y):
                    left_k = -half_a_box_y
                    right_k = 0.
                elif j == (size_y - half_a_box_y):
                    left_k = 0.
                    right_k = half_a_box_y
                else:
                    left_k = 0.
                    right_k = 0.
                if i == (half_a_box_x):
                    left_l = -half_a_box_x
                    right_l = 0
                elif i == (size_x - half_a_box_x):
                    left_l = 0
                    right_l = half_a_box_x
                else:
                    left_l = 0.
                    right_l = 0.
            else:
                left_l = 0.
                right_l = 0.
                left_k = 0.
                right_k = 0.

            logging.debug("left_l is " + str(left_l))
            logging.debug("left_k is " + str(left_k))
            logging.debug("right_l is " + str(right_l))
            logging.debug("right_k is " + str(right_k))

            logging.info(bcolors.FAIL+bcolors.UNDERLINE+"Starting downscale_field for index coordinates (%s, %s)" % (str(i), str(j)))

            # If both ranges exist:
            if range(int(left_k), int(right_k)) and range(int(left_l), int(right_l)):
                for k in range(int(left_k), int(right_k)):
                    for l in range(int(left_l), int(right_l)):
                        # logging.debug(str(i+l))
                        # logging.debug(str(j+k))
                        if mask[i + l, j + k] > 0:
                            # if ((max_height_lo == min_height_lo) or (len(max_height_lo) < 1)):
                            if (max_height_lo == min_height_lo):
                                field_hi[i + l, j + k] = field_lo[i + l, j + k]
                            else:
                                lapse = (min_value - max_value) / (max_height_lo - min_height_lo)
                                field_hi[i + l, j + k] = field_lo[i + l, j + k] + lapse * (elev_hi[i + l, j + k] - elev_lo[i + l, j + k])
            # Else both ranges are 0
            # else:
            #     if mask[i, j] > 0:
            #         lapse = (min_value - max_value) / (max_height_lo - min_height_lo)
            #         field_hi[i, j] = field_lo[i, j] + lapse * (elev_hi[i, j] - elev_lo[i, j])
            #         logging.debug("field_lo is: "+str(field_lo[i, j]))
            #         logging.debug("lapse is: "+str(lapse))
            #         logging.debug("elev_hi is: "+str(elev_hi[i, j]))
            #         logging.debug("elev_lo is: "+str(elev_lo[i, j]))

    logging.info("Finished! Total time is %s" % str((time.time() - now)))
    return field_hi


def main():
    args = parse_arguments()
    fmt = MyFormatter()
    hdlr = logging.StreamHandler(sys.stdout)
    hdlr.setFormatter(fmt)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(args.loglevel)
    # logging.basicConfig(format='%(name) - %(levelname)s: - %(message)s', level=args.loglevel)
    T_lo_varname = "TT"
    H_lo_varname = "SH"
    H_hi_varname = "SH"
    mask_varname = "MSK"

    T_lo = netcdf.netcdf_file(args.ifile_lo).variables[T_lo_varname].data[6, -1, :, :].squeeze()
    H_lo = netcdf.netcdf_file(args.ifile_lo).variables[H_lo_varname].data.squeeze()

    H_hi = netcdf.netcdf_file(args.ifile_hi).variables[H_hi_varname].data.squeeze()
    mask = netcdf.netcdf_file(args.ifile_hi).variables[mask_varname].data.squeeze()

    T_hi = downscale_field(T_lo, H_hi, H_lo, mask)

    ax1 = plt.subplot(131)
    m = ax1.contourf(T_lo)
    plt.colorbar(m)
    ax2 = plt.subplot(132)
    m = ax2.contourf(T_hi)
    plt.colorbar(m)
    ax3 = plt.subplot(133)
    m = ax3.contourf(mask)
    plt.colorbar(m)

    # plt.figure()
    # ax1 = plt.subplot(121)
    # ax1.contourf(H_hi)
    # ax2 = plt.subplot(122)
    # ax2.contourf(H_lo)
    plt.show()

if __name__ == '__main__':
    main()
