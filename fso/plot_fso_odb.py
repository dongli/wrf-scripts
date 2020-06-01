#!/usr/bin/env python3

import argparse
from glob import glob
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import cartopy.crs as crs
import numpy as np
from subprocess import run, PIPE

parser = argparse.ArgumentParser(description="Plot FSO result from ODB files.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--input-prefix', dest='input_prefix', help='Input ODB file prefix')
args = parser.parse_args()

file_paths = [file_path for file_path in sorted(glob(args.input_prefix + '*')) if not file_path.endswith('.pdf')]

cmd = f'odb sql "select *" -T -i {file_paths[1]}'
res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print(f'[Error]: Failed to run {cmd}!')
	exit(1)

obs_impact = {}
for line in res.stdout.decode('utf-8').strip().split('\n'):
	obs_type, impact = line.split()
	obs_impact[obs_type.replace("'", '')] = float(impact)

cmd = f'odb sql "select *" -T -i {file_paths[2]}'
res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print(f'[Error]: Failed to run {cmd}!')
	exit(1)

var_impact = {}
for line in res.stdout.decode('utf-8').strip().split('\n'):
	var_type, impact = line.split()
	var_impact[var_type.replace("'", '')] = float(impact)

p = (1000,950,900,850,800,750,700,650,600,550,500,400,300,200,100)
sound_lev_impact = { 'u': {}, 'v': {}, 't': {}, 'q': {} }
for k in range(len(p)):
	for var in ('u', 'v', 't', 'q'):
		sound_lev_impact[var][p[k]] = []
	p1 = p[k] - 0.5 * (p[k] - (p[k+1] if k != len(p) - 1 else p[-1] - 50))
	p2 = p[k] + 0.5 * ((p[k-1] if k != 0 else p[0] + 50) - p[k])
	cmd = f'''
odb sql \'select u_impact, u_qc, v_impact, v_qc, t_impact, t_qc, q_impact, q_qc
where obs_type="sound" and p>={p1*100} and p<={p2*100}\' -T -i {file_paths[0]}
'''
	res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	if res.returncode != 0:
		print(f'[Error]: Failed to run {cmd}!')
		exit(1)
	for line in res.stdout.decode('utf-8').strip().split('\n'):
		lev = {}
		columns = line.split()
		if len(columns) == 0:
			print(f'[Warning]: Empty record at {p[k]} pressure level!')
			continue
		u_impact = columns[0]; u_qc = columns[1]
		if u_impact != 'NULL' and u_qc in ('0', '2'): sound_lev_impact['u'][p[k]].append(float(u_impact))
		v_impact = columns[2]; v_qc = columns[3]
		if v_impact != 'NULL' and v_qc in ('0', '2'): sound_lev_impact['v'][p[k]].append(float(v_impact))
		t_impact = columns[4]; t_qc = columns[5]
		if t_impact != 'NULL' and t_qc in ('0', '2'): sound_lev_impact['t'][p[k]].append(float(t_impact))
		q_impact = columns[6]; q_qc = columns[7]
		if q_impact != 'NULL' and q_qc in ('0', '2'): sound_lev_impact['q'][p[k]].append(float(q_impact))

# p = (1000,950,900,850,800,750,700,650,600,550,500,400,300,200,100)
# profiler_lev_impact = { 'u': {}, 'v': {} }
# for k in range(len(p)):
# 	for var in ('u', 'v'):
# 		profiler_lev_impact[var][p[k]] = []
# 	p1 = p[k] - 0.5 * (p[k] - (p[k+1] if k != len(p) - 1 else p[-1] - 50))
# 	p2 = p[k] + 0.5 * ((p[k-1] if k != 0 else p[0] + 50) - p[k])
# 	cmd = f'''
# odb sql \'select u_impact, u_qc, v_impact, v_qc
# where obs_type="profiler" and p>={p1*100} and p<={p2*100}\' -T -i {file_paths[0]}
# '''
# 	res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
# 	if res.returncode != 0:
# 		print(f'[Error]: Failed to run {cmd}!')
# 		exit(1)
# 	for line in res.stdout.decode('utf-8').strip().split('\n'):
# 		lev = {}
# 		columns = line.split()
# 		if len(columns) == 0:
# 			print(f'[Warning]: Empty record at {p[k]} pressure level!')
# 			continue
# 		u_impact = columns[0]; u_qc = columns[1]
# 		if u_impact != 'NULL' and u_qc in ('0', '2'): profiler_lev_impact['u'][p[k]].append(float(u_impact))
# 		v_impact = columns[2]; v_qc = columns[3]
# 		if v_impact != 'NULL' and v_qc in ('0', '2'): profiler_lev_impact['v'][p[k]].append(float(v_impact))

synop_impact = { 'u': {}, 'v': {}, 't': {}, 'q': {} }
for var in ('u', 'v', 't', 'q'):
	cmd = f'''
odb sql \'select sid, lon, lat, {var}_impact, {var}_qc
where obs_type="synop"\' -T -i {file_paths[0]}
'''
	res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	if res.returncode != 0:
		print(f'[Error]: Failed to run {cmd}!')
	for line in res.stdout.decode('utf-8').strip().split('\n'):
		columns = line.split()
		if len(columns) == 0:
			print(f'[Warning]: Empty record!')
			continue
		if columns[3] != 'NULL' and columns[4] in ('0', '2'):
			synop_impact[var][columns[0]] = {
				'lon': float(columns[1]),
				'lat': float(columns[2]),
				'impact': float(columns[3])
			}

pdf = PdfPages(f'{args.input_prefix}.pdf')

fig = plt.figure(figsize=(8, 5))
plt.barh(list(obs_impact.keys()), list(obs_impact.values()), color='blue', height=0.8, zorder=2)
plt.gca().set_xlabel('Observation Impact')
plt.gca().set_ylabel('Observation Type')
plt.gca().yaxis.tick_right()
plt.grid(True, color='gray', zorder=1)
plt.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
pdf.savefig()

fig = plt.figure(figsize=(6, 4))
plt.barh(list(var_impact.keys()), list(var_impact.values()), color='blue', height=0.2, zorder=2)
plt.gca().set_xlabel('Observation Impact')
plt.gca().set_ylabel('Variable Type')
plt.gca().yaxis.tick_right()
plt.grid(True, color='gray', zorder=1)
plt.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
pdf.savefig()

for var_type, levels in sound_lev_impact.items():
	impact = []
	for _, var_impact in levels.items():
		impact.append(sum(var_impact))
	fig = plt.figure(figsize=(6, 4))
	plt.barh(list(levels.keys()), impact, color='blue', height=20, zorder=2)
	plt.gca().set_xlabel(f'Impact of {var_type}@sound')
	plt.gca().set_ylabel('Pressure Levels')
	plt.gca().yaxis.tick_right()
	plt.gca().invert_yaxis()
	plt.grid(True, color='gray', zorder=1)
	plt.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
	pdf.savefig()

# for var_type, levels in profiler_lev_impact.items():
# 	impact = []
# 	for _, var_impact in levels.items():
# 		impact.append(sum(var_impact))
# 	fig = plt.figure(figsize=(6, 4))
# 	plt.barh(list(levels.keys()), impact, color='blue', height=20, zorder=2)
# 	plt.gca().set_xlabel(f'Impact of {var_type}@profiler')
# 	plt.gca().set_ylabel('Pressure Levels')
# 	plt.gca().yaxis.tick_right()
# 	plt.gca().invert_yaxis()
# 	plt.grid(True, color='gray', zorder=1)
#		plt.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
# 	pdf.savefig()

proj = crs.PlateCarree()

for var in ('u', 'v', 't', 'q'):
	fig = plt.figure(figsize=(6, 4))
	ax = fig.add_subplot(1, 1, 1, projection=proj)
	ax.set_title(f'Variable: {var}')
	lon = [x['lon'] for _, x in synop_impact[var].items()]
	lat = [x['lat'] for _, x in synop_impact[var].items()]
	impact = [x['impact'] for _, x in synop_impact[var].items()]
	impact_lim = max((abs(min(impact)), abs(max(impact))))
	im = ax.scatter(lon, lat, c=impact, cmap='bwr', vmin=-impact_lim, vmax=impact_lim)
	pdf.savefig()

pdf.close()
