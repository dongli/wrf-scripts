#!/usr/bin/env python3

import re
import os
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader as ShapeReader
from cartopy.feature import ShapelyFeature, COASTLINE
from palettable.colorbrewer.diverging import RdBu_10_r, RdYlGn_4

def missing(value):
	return np.nan if value == -888888 else value

data = {}

read_synop = False
read_sound = False
num_record = 0
with open('gts_omb_oma_01') as file:
	for line in file.readlines():
		if 'synop' in line:
			num_record = int(line.split()[1])
			read_synop = True
			data['synop'] = []
			continue
		elif 'sound' in line:
			num_record = int(line.split()[1])
			read_sound = True
			data['sound'] = []
			continue
		if read_synop and num_record >= 0:
			if re.match(r'\s*\d+\s*$', line):
				n = int(line)
				num_record -= 1
				continue
			if n > 0:
				cols  = line.split()
				sid   = cols[1][-5:]
				lat   = missing(float(cols[2]))
				lon   = missing(float(cols[3]))
				u     = missing(float(cols[5]))
				u_omb = missing(float(cols[6]))
				u_qc  = missing(float(cols[7]))
				u_err = missing(float(cols[8]))
				u_oma = missing(float(cols[9]))
				v     = missing(float(cols[10]))
				v_omb = missing(float(cols[11]))
				v_qc  = missing(float(cols[12]))
				v_err = missing(float(cols[13]))
				v_oma = missing(float(cols[14]))
				t     = missing(float(cols[15]))
				t_omb = missing(float(cols[16]))
				t_qc  = missing(float(cols[17]))
				t_err = missing(float(cols[18]))
				t_oma = missing(float(cols[19]))
				p     = missing(float(cols[20]))
				p_omb = missing(float(cols[21]))
				p_qc  = missing(float(cols[22]))
				p_err = missing(float(cols[23]))
				p_oma = missing(float(cols[24]))
				q     = missing(float(cols[25]))
				q_omb = missing(float(cols[26]))
				q_qc  = missing(float(cols[27]))
				q_err = missing(float(cols[28]))
				q_oma = missing(float(cols[29]))
				data['synop'].append({
					'sid': sid,
					'lon': lon,
					'lat': lat,
					'p': p,
					'p_omb': p_omb,
					'p_qc': p_qc,
					'p_err': p_err,
					'p_oma': p_oma,
					'u': u,
					'u_omb': u_omb,
					'u_qc': u_qc,
					'u_err': u_err,
					'u_oma': u_oma,
					'v': v,
					'v_omb': v_omb,
					'v_qc': v_qc,
					'v_err': v_err,
					'v_oma': v_oma,
					't': t,
					't_omb': t_omb,
					't_qc': t_qc,
					't_err': t_err,
					't_oma': t_oma,
					'q': q,
					'q_omb': q_omb,
					'q_qc': q_qc,
					'q_err': q_err,
					'q_oma': q_oma,
				})
				n -= 1
		if read_sound and num_record >= 0:
			if re.match(r'\s*\d+\s*$', line):
				n = int(line)
				num_record -= 1
				continue
			if n > 0:
				cols  = line.split()
				sid   = cols[1][-5:]
				lat   = missing(float(cols[2]))
				lon   = missing(float(cols[3]))
				p     = missing(float(cols[4]))
				u     = missing(float(cols[5]))
				u_omb = missing(float(cols[6]))
				u_qc  = missing(float(cols[7]))
				u_err = missing(float(cols[8]))
				u_oma = missing(float(cols[9]))
				v     = missing(float(cols[10]))
				v_omb = missing(float(cols[11]))
				v_qc  = missing(float(cols[12]))
				v_err = missing(float(cols[13]))
				v_oma = missing(float(cols[14]))
				t     = missing(float(cols[15]))
				t_omb = missing(float(cols[16]))
				t_qc  = missing(float(cols[17]))
				t_err = missing(float(cols[18]))
				t_oma = missing(float(cols[19]))
				q     = missing(float(cols[20]))
				q_omb = missing(float(cols[21]))
				q_qc  = missing(float(cols[22]))
				q_err = missing(float(cols[23]))
				q_oma = missing(float(cols[24]))
				data['sound'].append({
					'sid': sid,
					'lon': lon,
					'lat': lat,
					'p': p,
					'u': u,
					'u_omb': u_omb,
					'u_qc': u_qc,
					'u_err': u_err,
					'u_oma': u_oma,
					'v': v,
					'v_omb': v_omb,
					'v_qc': v_qc,
					'v_err': v_err,
					'v_oma': v_oma,
					't': t,
					't_omb': t_omb,
					't_qc': t_qc,
					't_err': t_err,
					't_oma': t_oma,
					'q': q,
					'q_omb': q_omb,
					'q_qc': q_qc,
					'q_err': q_err,
					'q_oma': q_oma,
				})
				n -= 1

def plot(lon, lat, values, vmin, vmax, title, pdf, cmap=RdBu_10_r, colorbar=True):
	proj = ccrs.PlateCarree()
	
	fig = plt.figure(figsize=(12, 8))
	ax = plt.axes(projection=proj)
	ax.set_extent([73, 135, 15, 55], crs=proj)
	ax.gridlines(crs=proj, draw_labels=True, linewidth=1, color='k', alpha=0.5, linestyle='--')

	if os.path.isfile('/opt/china-shapefiles/shapefiles/china.shp'):
		china = ShapelyFeature(
			ShapeReader('/opt/china-shapefiles/shapefiles/china.shp').geometries(),
			proj,
			edgecolor='grey',
			facecolor='none'
		)
		ax.add_feature(china)
	else:
		print('You can run the following command to get China official shapefiles.')
		print('# cd /opt')
		print('# git clone https://github.com/dongli/china-shapefiles')
	ax.add_feature(COASTLINE.with_scale('50m'), linewidth=0.5)

	p = ax.scatter(lon, lat, s=2.0, c=values, vmin=vmin, vmax=vmax, cmap=cmap.mpl_colormap)
	if colorbar:
		fig.colorbar(p, orientation='horizontal', extend='both', spacing='proportional', aspect=40, pad=0.05)
	ax.set_title(title)

	pdf.savefig()
	plt.close()

with PdfPages('gts_omb_oma_01.pdf') as pdf:
	if 'synop' in data:
		df = pd.DataFrame(data['synop'])
		plot(df.lon, df.lat, df.p_omb,   -400,   400, 'SYNOP: Pressure OMB', pdf)
		plot(df.lon, df.lat, df.p_oma,   -400,   400, 'SYNOP: Pressure OMA', pdf)
		plot(df.lon, df.lat, df.u_omb,     -5,     5, 'SYNOP: Wind u-component OMB', pdf)
		plot(df.lon, df.lat, df.u_oma,     -5,     5, 'SYNOP: Wind u-component OMA', pdf)
		plot(df.lon, df.lat, df.v_omb,     -5,     5, 'SYNOP: Wind v-component OMB', pdf)
		plot(df.lon, df.lat, df.v_oma,     -5,     5, 'SYNOP: Wind v-component OMA', pdf)
		plot(df.lon, df.lat, df.t_omb,     -8,     8, 'SYNOP: Temperature OMB', pdf)
		plot(df.lon, df.lat, df.t_oma,     -8,     8, 'SYNOP: Temperature OMA', pdf)
		plot(df.lon, df.lat, df.q_omb, -0.005, 0.005, 'SYNOP: Specific humidity OMB', pdf)
		plot(df.lon, df.lat, df.q_oma, -0.005, 0.005, 'SYNOP: Specific humidity OMA', pdf)
		plot(df.lon, df.lat, [1 if x > 0 else -1 for x in abs(df.p_omb) - abs(df.p_oma)], -1, 1, 'SYNOP: Pressure OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(df.lon, df.lat, [1 if x > 0 else -1 for x in abs(df.u_omb) - abs(df.u_oma)], -1, 1, 'SYNOP: Wind u-component OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(df.lon, df.lat, [1 if x > 0 else -1 for x in abs(df.v_omb) - abs(df.v_oma)], -1, 1, 'SYNOP: Wind v-component OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(df.lon, df.lat, [1 if x > 0 else -1 for x in abs(df.t_omb) - abs(df.t_oma)], -1, 1, 'SYNOP: Temperature OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(df.lon, df.lat, [1 if x > 0 else -1 for x in abs(df.q_omb) - abs(df.q_oma)], -1, 1, 'SYNOP: Specific humidity OMB vs OMA', pdf, RdYlGn_4, colorbar=False)

	if 'sound' in data:
		df = pd.DataFrame(data['sound'])
		plev = df.loc[df['p'] == 85000]
		plot(plev.lon, plev.lat, plev.u_omb,     -5,      5, 'SOUND@850hPa: Wind u-component OMB', pdf)
		plot(plev.lon, plev.lat, plev.u_oma,     -5,      5, 'SOUND@850hPa: Wind u-component OMA', pdf)
		plot(plev.lon, plev.lat, plev.v_omb,     -5,      5, 'SOUND@850hPa: Wind v-component OMB', pdf)
		plot(plev.lon, plev.lat, plev.v_oma,     -5,      5, 'SOUND@850hPa: Wind v-component OMA', pdf)
		plot(plev.lon, plev.lat, plev.t_omb,     -8,      8, 'SOUND@850hPa: Temperature OMB', pdf)
		plot(plev.lon, plev.lat, plev.t_oma,     -8,      8, 'SOUND@850hPa: Temperature OMA', pdf)
		plot(plev.lon, plev.lat, plev.q_omb, -0.005,  0.005, 'SOUND@850hPa: Specific humidity OMB', pdf)
		plot(plev.lon, plev.lat, plev.q_oma, -0.005,  0.005, 'SOUND@850hPa: Specific humidity OMA', pdf)

		plot(plev.lon, plev.lat, [1 if x > 0 else -1 for x in abs(plev.u_omb) - abs(plev.u_oma)], -1, 1, 'SOUND@850hPa: Wind u-component OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(plev.lon, plev.lat, [1 if x > 0 else -1 for x in abs(plev.v_omb) - abs(plev.v_oma)], -1, 1, 'SOUND@850hPa: Wind v-component OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(plev.lon, plev.lat, [1 if x > 0 else -1 for x in abs(plev.t_omb) - abs(plev.t_oma)], -1, 1, 'SOUND@850hPa: Temperature OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
		plot(plev.lon, plev.lat, [1 if x > 0 else -1 for x in abs(plev.q_omb) - abs(plev.q_oma)], -1, 1, 'SOUND@850hPa: Specific humidity OMB vs OMA', pdf, RdYlGn_4, colorbar=False)
