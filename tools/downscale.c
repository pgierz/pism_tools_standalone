3#include <stdlib.h>
#include <stdio.h>
#include <netcdf.h>

/* This is the name of the data file we will read. */
#define FILE_NAME "test.nc"

/* We are reading 2D data, a 6 x 12 grid. */
#define NX 96
#define NY 48

/* Handle errors by printing an error message and exiting with a
 * non-zero status. */
#define ERRCODE 2
#define ERR(e) {printf("Error: %s\n", nc_strerror(e)); exit(ERRCODE);}

/* PG: Make an array...? */
double downscale_field[NX][NY];
printf("*** NEW array made! \n");
printf("%s", downscale_field);
  
int main() {
  /* printf("PG: Hello! \n"); */
  /* There will be netCDF IDs for the file, each group, and each
   * variable. */
  int ncid, varid1, grp1id;
  unsigned long long data_in[NX][NY];
  /* Loop indexes, and error handling. */
  int x, y, retval;
  /* The following struct is written as a compound type. */
  struct s1 
  {
    int i1;
    int i2;
  };
  struct s1 compound_data[NX][NY];
  /* Open the file. NC_NOWRITE tells netCDF we want read-only access
   * to the file.*/

  /* printf("PG: Opening file... \n"); */
  if ((retval = nc_open(FILE_NAME, NC_NOWRITE, &ncid)))
    ERR(retval);
  /* printf("PG: Done!\n"); */

  /* Get the group ids of our two groups. */
  /* printf("PG: Getting gids... \n"); */
  if ((retval = nc_inq_ncid(ncid, "temp2", &grp1id)))
    ERR(retval);
  /* printf("PG: Done!\n"); */

  /* Get the varid of the uint64 data variable, based on its name, in
   * grp1. */
  if ((retval = nc_inq_varid(grp1id, "temp2", &varid1))) 
    ERR(retval);
  /* Read the data. */
  if ((retval = nc_get_var_ulonglong(grp1id, varid1, &data_in[0][0])))
    ERR(retval);
  
  /* Check the data */
  for (x = 0; x < NX; x++) {
    for (y = 0; y < NY; y++) {
      printf("%d ",data_in[x][y]);
    }
  }

  /* Close the file, freeing all resources. */
  if ((retval = nc_close(ncid)))
    ERR(retval);


  
  printf("*** SUCCESS reading example file %s!\n", FILE_NAME);
  return 0;
}

