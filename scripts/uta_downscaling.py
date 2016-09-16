#!/usr/bin/env python
# coding: utf-8

import numpy as np
import time


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


def downscale_field(T, elev_hi, elev_lo, mask, half_a_box):
    """
    Downscaling routine based upon MATLAB function written by Uta Krebs-Kanzow

    Paul J. Gierz, Fri Sep 16 10:25:20 2016

    Keyword Arguments:
    T          -- input temperature from coarse grid (is this already resampled?)
    elev_hi    -- orographic information of the high resolution grid
    elev_lo    -- orographic information of the low resolution grid; resampled to the high resolution grid
                  Assuming hi-res is 9x better resolved: If on lo-res (x1, y1) = 50, (x2, y1) = 75, then on hi-res
                  (x1, y1) = 50, (x2, y1) = 50, (x3, y1) = 50, (x4, y1)=75, (x5, y1) = 75, (x6, y1) = 75
    mask       -- Mask of ice sheet domain to use
    half_a_box -- size of half a box (?)
    """

    # TODO: Replace T with "field" for arbitrary fields
    # TODO: array checks

    downscaled = np.empty(T.shape).fill(np.nan)

    factor = 0.8                # PG: compensates for different x and y resolutions
    half_a_box_x = round(factor * half_a_box)
    half_a_box_y = round(half_a_box)

    size_x, size_y = T.shape

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

                    # PG: The following two variables don't seem to be used
                    #
                    # min_height_hi = np.nanmin(
                    #     elev_hi[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                    # max_height_hi = np.nanmax(
                    #     elev_hi[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                    min_height_lo = np.nanmin(
                        elev_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                    max_height_lo = np.nanmax(
                        elev_lo[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

                    min_value = np.nanmin(
                        T[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])
                    max_value = np.nanmax(
                        T[i - half_a_box_x:i + half_a_box_x, j - half_a_box_y:j + half_a_box_y])

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
                            downscaled[i + l, j + k] = T[i + l, j + k]
                        else:
                            downscaled[i + l, j + k] = T[i + l, j + k] + ((min_value - max_value) / (
                                max_height_lo - min_height_lo)) * (elev_hi[i + l, j + k] - elev_lo[i + l, j + k])
    print_info("Finished! Total time is %s" % str((time.time() - now)))
    return downscaled
