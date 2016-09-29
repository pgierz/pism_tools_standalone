rlon=ncread('/csys/nobackup1_PALEO/ukrebska/MAR_data/ICE.2013.01-08.f07.nc','LON');
rlat=ncread('/csys/nobackup1_PALEO/ukrebska/MAR_data/ICE.2013.01-08.f07.nc','LAT');
%rlon=360+rlon
rlon=double(rlon);
rlat=double(rlat);
dx_cent=diff(rlon);
dy_cent=diff(rlat,'',2);


  rlon_corn= .25*(rlon(1:end-1,1:end-1)+rlon(2:end,1:end-1)+...
                  rlon(1:end-1,2:end)  + rlon(2:end,2:end));
  rlat_corn= .25*(rlat(1:end-1,1:end-1)+rlat(2:end,1:end-1)+...
                  rlat(1:end-1,2:end)  + rlat(2:end,2:end));

rlon_corn=[rlon_corn(:,1) rlon_corn rlon_corn(:,end)];
rlat_corn=[rlat_corn(1,:); rlat_corn; rlat_corn(end,:)];
rlon_corn=[2*rlon_corn(1,:)-rlon_corn(2,:); rlon_corn; 2*rlon_corn(end,:)-rlon_corn(end-1,:)];
rlat_corn=[2*rlat_corn(:,1)-rlat_corn(:,2) rlat_corn 2*rlat_corn(:,end)-rlat_corn(:,end-1)];

rlon_ll=rlon_corn(1:end-1,1:end-1);
rlat_ll=rlat_corn(1:end-1,1:end-1);
rlon_ul=rlon_corn(1:end-1,2:end);
rlat_ul=rlat_corn(1:end-1,2:end);
rlon_lr=rlon_corn(2:end,1:end-1);
rlat_lr=rlat_corn(2:end,1:end-1);
rlon_ur=rlon_corn(2:end,2:end);
rlat_ur=rlat_corn(2:end,2:end);

xbounds=[rlon_ul(:) rlon_ll(:) rlon_lr(:) rlon_ur(:)];
ybounds=[rlat_ul(:) rlat_ll(:) rlat_lr(:) rlat_ur(:)];
%xbounds=xbounds(:)';
%ybounds=ybounds(:)';
save -ascii MAR_rlon rlon
save -ascii MAR_rlat rlat
save -ascii MAR_xbounds xbounds
save -ascii MAR_ybounds ybounds

%cornerx=[rlon_ul(:) rlon 
