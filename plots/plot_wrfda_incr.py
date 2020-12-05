#!/usr/bin/env python3

from plot_common import *

k = int(sys.argv[1]) if len(sys.argv) > 1 else 0

ds_fg = xr.open_dataset('fg')

ds_wrfvar_output = xr.open_dataset('wrfvar_output')

lon_u = ds_fg.XLONG_U[0,:,:]
lat_u = ds_fg.XLAT_U[0,:,:]
lon_v = ds_fg.XLONG_V[0,:,:]
lat_v = ds_fg.XLAT_V[0,:,:]
lon   = ds_fg.XLONG[0,:,:]
lat   = ds_fg.XLAT[0,:,:]

fig.suptitle(f'Level index {k}')

ax1 = get_china_ax(fig, 221)
plt.colorbar(ax1.contourf(lon_u, lat_u, ds_wrfvar_output.U[0,k,:,:] - ds_fg.U[0,k,:,:]))
ax1.set_title('U increment')

ax2 = get_china_ax(fig, 222)
plt.colorbar(ax2.contourf(lon_v, lat_v, ds_wrfvar_output.V[0,k,:,:] - ds_fg.V[0,k,:,:]))
ax2.set_title('V increment')

ax3 = get_china_ax(fig, 223)
plt.colorbar(ax3.contourf(lon, lat, ds_wrfvar_output.T[0,k,:,:] - ds_fg.T[0,k,:,:]))
ax3.set_title('T increment')

ax4 = get_china_ax(fig, 224)
plt.colorbar(ax4.contourf(lon, lat, ds_wrfvar_output.P[0,k,:,:] - ds_fg.P[0,k,:,:]))
ax4.set_title('P increment')

plt.show()
plt.close()
