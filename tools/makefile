NETCDF_FLAGS = -L/global/AWIsoft/netcdf/4.4.0_gnu/lib -lnetcdff -lnetcdf

default: downscale

downscale.o: downscale.c 
	gcc -c downscale.c -o downscale.o

downscale: downscale.o
	gcc downscale.o -o downscale $(NETCDF_FLAGS)

clean:
	rm -f downscale.o
	rm -f downscale


