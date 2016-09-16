#!/usr/bin/env python

import osr
import netCDF4 as nc
import numpy as np
import sys
import getopt
from argparse import ArgumentParser


def convert_file(filename, opts={}):
    inSpatialRef = osr.SpatialReference()  # orig projection
    if "utm" in opts.keys() and opts["utm"] is not None:
        inSpatialRef.SetProjCS(
            "UTM %i (WGS84) in northern hemisphere." % (opts["utm"]))
        inSpatialRef.SetWellKnownGeogCS("WGS84")
        inSpatialRef.SetUTM(opts["utm"], True)
    else:  # (opts.get("polar_stereographic", False)):
        inSpatialRef.ImportFromEPSG(3413)  # Polar Stereographic
        #    else:
        #        inSpatialRef.ImportFromEPSG(3338) # Alaska Albers
    outSpatialRef = osr.SpatialReference()  # target projection
    outSpatialRef.ImportFromEPSG(4326)  # WGS 1984
    coordTransform = osr.CoordinateTransformation(
        inSpatialRef, outSpatialRef)  # create converter
    # display information on orig projection
    print inSpatialRef.ExportToPrettyWkt()
    # outSpatialRef.ExportToPrettyWkt()
    # coordTransform.TransformPoint(1.4e6,1e6) # transform a sample point from
    # AA to WGS

    # infile=nc.Dataset(filename,"r")
    # #infile=nc.Dataset("test.nc","r")
    print "hellop"
    # x=infile.variables["x"][:]
    # y=infile.variables["y"][:]
    x = np.arange(-5995000, 5996000, 10000)
    y = np.arange(-5995000, 5996000, 10000)

    xx = np.expand_dims(x, axis=0).repeat(
        len(y), axis=0).reshape(len(x) * len(y))  # .transpose()
    yy = np.expand_dims(y, axis=0).repeat(
        len(x), axis=0).transpose().reshape(len(x) * len(y))

    # print (xx)
    # print (yy)
    # print (np.array((xx,yy)).transpose()).shape
    out = np.array(coordTransform.TransformPoints(
        np.array((xx, yy)).transpose())).reshape((len(x), len(y), 3))
    outfile = nc.Dataset("ll_%s" % (filename), "w", format='NETCDF3_64BIT')
    fdx = outfile.createDimension("x", len(x))
    fdy = outfile.createDimension("y", len(y))
    fdy = outfile.createDimension("grid_corners", 4)

    fvx = outfile.createVariable("x", "f4", ("x",))
    fvy = outfile.createVariable("y", "f4", ("y",))
    fvx[:] = x
    fvy[:] = y
    fvx.units = "m"
    fvy.units = "m"

    lon = outfile.createVariable("lon", "f4", ("y", "x"), fill_value=-9.e9)
    lat = outfile.createVariable("lat", "f4", ("y", "x"), fill_value=-9.e9)

    lon.units = "degrees"
    lon.long_name = "longitude"
    lon.standard_name = "longitude"
    lon.bounds = "grid_corner_lon"
    lon._CoordinateAxisType = "Lon"

    lat.units = "degrees"
    lat.long_name = "latitude"
    lat.standard_name = "latitude"
    lat.bounds = "grid_corner_lat"
    lat._CoordinateAxisType = "Lat"

    lon[:] = out[:, :, 0]
    lat[:] = out[:, :, 1]
    xoff = (x[1] - x[0]) / 2.
    yoff = (y[1] - y[0]) / 2.
    addx = [xoff, xoff, -xoff, -xoff]
    addy = [-yoff, yoff, yoff, -yoff]

    grid_corner_lat = outfile.createVariable(
        "grid_corner_lat", "f4", ("y", "x", "grid_corners"), fill_value=-9.e9)
    grid_corner_lon = outfile.createVariable(
        "grid_corner_lon", "f4", ("y", "x", "grid_corners"), fill_value=-9.e9)

    grid_corner_lat.units = "degrees"
    grid_corner_lon.units = "degrees"

    for i in xrange(4):
        corner_temp = np.array(coordTransform.TransformPoints(np.array(
            (xx + addx[i], yy + addy[i])).transpose())).reshape((len(x), len(y), 3))
        grid_corner_lon[:, :, i] = corner_temp[:, :, 0]
        grid_corner_lat[:, :, i] = corner_temp[:, :, 1]

    outfile.close()
    #################


def parse_args():
    parser = ArgumentParser()
    parser.description = "compare slopes of two variables from two files"
    parser.add_argument("FILES", nargs=1)
    parser.add_argument("-v", "--verbose",
                        help='''Be verbose''', action="store_true")
    parser.add_argument("-u", "--utm",
                        help='''File is using utm coordinates''', default=None, type=int)
    # parser.add_argument("-s", "--state",
    #                      help='''file with reference values''', required = True)
    # parser.add_argument("-b", "--var_b",
    #                    help='''variable b''', default="data")
    options = parser.parse_args()
    return options


def main():
    options = parse_args()
    if options.verbose:
        print (dir(options))
        print options.FILES
        # fu.debug = True
    convert_file(options.FILES[0], vars(options))
  

if __name__ == "__main__":
    main()
