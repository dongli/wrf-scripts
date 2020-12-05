import re
import os
import sys
import xarray as xr
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader as ShapeReader
from cartopy.feature import ShapelyFeature, COASTLINE

fig = plt.figure(figsize=(12, 8))

def get_china_ax(fig=None, subplot=111, min_lon=73, max_lon=135, min_lat=15, max_lat=55, proj=None):
	if proj == None: proj = ccrs.PlateCarree()
	if fig:
		ax = fig.add_subplot(subplot, projection=proj)
	else:
		ax = plt.subplot(subplot, projection=proj)
	ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=proj)
	gl = ax.gridlines(crs=proj, draw_labels=True, linewidth=1, color='k', alpha=0.5, linestyle='--')
	gl.right_labels = False
	gl.top_labels = False

	if os.path.isfile('/opt/china-shapefiles/shapefiles/china.shp'):
		china = ShapelyFeature(
			ShapeReader('/opt/china-shapefiles/shapefiles/china.shp').geometries(),
			proj,
			linewidth=0.1,
			edgecolor='grey',
			facecolor='none'
		)
		ax.add_feature(china)
	else:
		print('You can run the following command to get China official shapefiles.')
		print('# cd /opt')
		print('# git clone https://github.com/dongli/china-shapefiles')
	ax.add_feature(COASTLINE.with_scale('50m'), linewidth=0.5)

	return ax
