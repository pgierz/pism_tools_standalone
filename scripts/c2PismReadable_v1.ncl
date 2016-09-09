begin
   fname = "remap.nc"
   fnameg = "grid_10km.nc"
   fnameo = "forcing_lgm_v2.nc"

   ;================================
   system("rm -f  " + fnameo)
   out = addfile(fnameo,"c")


   ;====== grid file ===============
   grid = addfile(fnameg,"r")
   ;******  x  **********
   x = grid->x
   delete_VarAtts(x,-1)
   x@axis = "X"
   x@units = "m"
   x@long_name = "X-coordinate in Cartesian system"
   x@standard_name = "projection_x_coordinate"
   out->x = x
   ;******  y  *********
   y = grid->y
   delete_VarAtts(y,-1)
   y@axis = "Y"
   y@units = "m"
   y@long_name = "Y-coordinate in Cartesian system"
   y@standard_name = "projection_y_coordinate"
   out->y = y
   ;****** lat *********
   lat = grid->lat
   delete_VarAtts(lat,-1)
   lat@standard_name = "latitude"
   lat@long_name = "latitude"
   lat@units = "degrees"
   out->lat = lat
   ;****** lon **********
   lon = grid->lon
   delete_VarAtts(lon,-1)
   lon@standard_name = "longitude"
   lon@long_name = "longitude"
   lon@units = "degrees"
   out->lon = lon
   ;*********  time *******************
   time = (/0.,31.,59.,90.,120.,151.,181.,212.,243.,273.,304.,334./)
   ;printVarSummary(time)
   filedimdef(out,"time",-1,True)
   time!0 = "time"
   time&time = (/time/)

   time@standard_name = "time"
   time@long_name = "time"
   time@units = "days since  01-01-01 00:00:00"
   time@calendar = "365_day"
   time@bounds = "time_bnds"
   out->time = time

   ;*********  time bounds *******************
   bnds = (/1.,2./)
   bnds!0 = "bnds"
   bnds&bnds = (/bnds/)
   out->bnds = bnds
   ;----------------
   time_bnds = new((/12,2/),float,"No_FillValue")
   time_bnds(:,0) = (/time(:)/)
   time_bnds(11,1) = 365.
   do n = 0, 10
     time_bnds(n,1) = time_bnds(n+1,0)
   end do
   time_bnds!0 = "time"
   time_bnds!1 = "bnds"
   time_bnds&time = time&time
   time_bnds&bnds = bnds&bnds
   ;
   out->time_bnds = time_bnds

   ;====== airtemp file & precipitation file ================
   in = addfile(fname,"r")
   air = flt2dble(in->temp2)
   print("Is there any missing value for air temperature?  " + any(ismissing(air)))
   ;air@_FillValue = default_fillvalue("float")
   ;air@missing_value = default_fillvalue("double")
   air_temp = new((/dimsizes(air)/),double,"No_FillValue")
   air_temp = (/air/)
   ; K => degC
   air_temp = air_temp-273.15
   ;print(getvardims(air))
   air_temp!0 = "time"
   air_temp&time = time&time
   air_temp!1 = "y"
   air_temp&y = y&y
   air_temp!2 ="x"
   air_temp&x = x&x

   air_temp@standard_name = "air_temperature"
   air_temp@units = "degC"
   air_temp@long_name = "Surface air temperature at LGM "
   air_temp@coordinates = "lon lat"
   air_temp@grid_mapping = "mapping"
   out->air_temp = air_temp

   ;*******   precipitation  ************
   in = addfile(fname,"r")
   precip = flt2dble(in->precip)
   print("Is there any missing value for precip?  " + any(ismissing(precip)))
   precipitation = new(dimsizes(precip),typeof(precip),"No_FillValue")
   ;  kg/m^2s  => m/s ice equivalent
   precipitation = (/precip/)
   precipitation = precipitation/910.
   ; m/s => mm/day
   precipitation = precipitation*1000.*24.*3600.
   ;
   ;print(getvardims(precip))
   precipitation!0 = "time"
   precipitation&time = time&time
   precipitation!1 = "y"
   precipitation&y = y&y
   precipitation!2 = "x"
   precipitation&x = x&x
   ;
   precipitation@standard_name = "lwe_precipitation_rate"
   precipitation@long_name = "Total Precipitation at LGM"
   precipitation@units = "mm day-1"
   precipitation@coordinates = "lon lat"
   precipitation@grid_mapping = "mapping"
   ;
   out->precipitation = precipitation

   ;============= create global attribute of the file ==========
   fatt = True
   fatt@title = "climate forcing air temperature and precipitation time = 21ka LGM"
   fatt@creation_date = systemfunc("date")
   fileattdef(out,fatt)
   ;--------------------------

end

