#!/usr/bin/env python
# coding: utf-8

import numpy as np
import time
import argparse
from scipy.io import netcdf


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def debug(s):
    print bcolors.FAIL + "DEBUG: " + s + bcolors.ENDC


def print_info(s):
    print bcolors.HEADER + s + bcolors.ENDC



def parse_arguments():
    parser = argparse.ArgumentParser(description='Downscaling Script')
    parser.add_argument('ifile_lo', metavar="F", type=str,
                        help="The path of the input file to use (lo res)")
    parser.add_argument('ifile_hi', metavar="F", type=str,
                        help="The path of the input file to use (hi res)")
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

    # TODO: array checks

    field_hi = np.empty(field_lo.shape).fill(np.nan)

    factor = 0.8                # PG: compensates for different x and y resolutions
    half_a_box_x = round(factor * half_a_box)
    half_a_box_y = round(half_a_box)

    size_x, size_y = field_lo.shape

    now = time.time()
    print_info("Downscaling Temperature")
    print_info("Start...")
    for j in range(1 + half_a_box_y, size_y - half_a_box_y):
        for i in range(1 + half_a_box_x, size_x - half_a_box_x):
            debug("Set box index selection")
            if mask[i, j]:
                length_condition = True  # PG See Note below
                # NOTE: This needs to be as:
                #
                # (length(find(~isnan(T(i-half_a_boxx:i+half_a_boxx,j -half_a_boxy:j+half_a_boxy))))>0)
                #
                if length_condition:

                    min_height_lo = np.nanmin(
                        elev_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                    max_height_lo = np.nanmax(
                        elev_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                    min_value = np.nanmin(
                        field_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                    max_value = np.nanmax(
                        field_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                    if j == (1 + half_a_box_y):
                        left_k = -half_a_box_y
                        right_k = 0.
                    elif j == (size_y - half_a_box_y):
                        left_k = 0.
                        right_k = half_a_box_y
                    else:
                        left_k = 0.
                        right_k = 0.
                if i == (1 + half_a_box_x):
                    left_l = -half_a_box_x
                    right_l = 0
                elif i == (size_x - half_a_box_x):
                    left_l = 0
                    right_l = half_a_box_x
                else:
                    left_l = 0.
                    right_l = 0.
            debug("Downscale part")
            for k in range(left_k, right_k):
                for l in range(left_l, right_l):
                    if mask[i + l, j + k] > 0:
                        if ((max_height_lo == min_height_lo) or (len(max_height_lo) < 1)):
                            field_hi[i + l, j + k] = field_lo[i + l, j + k]
                        else:
                            lapse = (min_value - max_value) / (max_height_lo - min_height_hi)
                            field_hi[i + l, j + k] = field_lo[i + l, j + k] + lapse * (elev_hi[i + l, j + k] - elev_lo[i + l, j + k])
    print_info("Finished! Total time is %s" % str((time.time() - now)))
    return field_hi


def main():
    args = parse_arguments()
    
    T_lo_varname = "ST"
    H_lo_varname = "SH"
    H_hi_varname = "SH"
    mask_varname = "MSK"

    T_lo = netcdf.netcdf_file(args.ifile_lo).variables[T_lo_varname].data.squeeze()
    H_lo = netcdf.netcdf_file(args.ifile_lo).variables[H_lo_varname].data.squeeze()

    H_hi = netcdf.netcdf_file(args.ifile_hi).variables[H_hi_varname].data.squeeze()
    mask = netcdf.netcdf_file(args.ifile_hi).variables[mask_varname].data.squeeze()
    
    print T_lo, H_lo, H_hi, mask
    


if __name__ == '__main__':
    main()
