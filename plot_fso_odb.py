#!/usr/bin/env python3

import argparse
from glob import glob
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from subprocess import run, PIPE

parser = argparse.ArgumentParser(description="Plot FSO result from ODB files.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-i', '--input-prefix', dest='input_prefix', help='Input ODB file prefix')
args = parser.parse_args()

file_paths = glob(args.input_prefix + '*')

cmd = f'odb sql "select *" -T -i {file_paths[0]}'
res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print('[Error]: Failed to run {cmd}!')
	exit(1)

obs_impact = {}
for line in res.stdout.decode('utf-8').strip().split('\n'):
	obs_type, impact = line.split()
	obs_impact[obs_type.replace("'", '')] = float(impact)

cmd = f'odb sql "select *" -T -i {file_paths[1]}'
res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print('[Error]: Failed to run {cmd}!')
	exit(1)

var_impact = {}
for line in res.stdout.decode('utf-8').strip().split('\n'):
	var_type, impact = line.split()
	var_impact[var_type.replace("'", '')] = float(impact)

p = (1000,950,900,850,800,750,700,650,600,550,500,400,300,200,100)
lev_impact = { 'u': {}, 'v': {}, 't': {}, 'q': {} }
for k in range(len(p)):
	for var in ('u', 'v', 't', 'q'):
		lev_impact[var][p[k]] = []
	p1 = p[k+1] if k != len(p) - 1 else p[-1] - 50
	p2 = p[k-1] if k != 0 else p[0] + 50
	cmd = f'odb sql \'select * where obs_type="sound" and p>={p1*100} and p<={p2*100}\' -T -i {file_paths[2]}'
	res = run(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	if res.returncode != 0:
		print(f'[Error]: Failed to run {cmd}!')
		exit(1)
	for line in res.stdout.decode('utf-8').strip().split('\n'):
		lev = {}
		columns = line.split()
		if len(columns) == 0:
			print(f'[Error]: Empty record at {p[k]} pressure level!')
			exit(1)
		u_impact = columns[4]; u_qc = columns[5]
		if u_impact != 'NULL' and u_qc == '0': lev_impact['u'][p[k]].append(float(u_impact))
		v_impact = columns[9]; v_qc = columns[10]
		if v_impact != 'NULL' and v_qc == '0': lev_impact['v'][p[k]].append(float(v_impact))
		t_impact = columns[14]; t_qc = columns[15]
		if t_impact != 'NULL' and t_qc == '0': lev_impact['t'][p[k]].append(float(t_impact))
		q_impact = columns[24]; q_qc = columns[25]
		if q_impact != 'NULL' and q_qc == '0': lev_impact['q'][p[k]].append(float(q_impact))

pdf = PdfPages(f'{args.input_prefix}.pdf')

fig = plt.figure(figsize=(8, 5))
plt.barh(list(obs_impact.keys()), list(obs_impact.values()), color='blue', height=0.8, zorder=2)
plt.gca().set_xlabel('Observation Impact')
plt.gca().set_ylabel('Observation Type')
plt.gca().yaxis.tick_right()
plt.grid(True, color='gray', zorder=1)
pdf.savefig()

fig = plt.figure(figsize=(6, 4))
plt.barh(list(var_impact.keys()), list(var_impact.values()), color='blue', height=0.2, zorder=2)
plt.gca().set_xlabel('Observation Impact')
plt.gca().set_ylabel('Variable Type')
plt.gca().yaxis.tick_right()
plt.grid(True, color='gray', zorder=1)
pdf.savefig()

for var_type, levels in lev_impact.items():
	impact = []
	for _, var_impact in levels.items():
		impact.append(sum(var_impact))
	fig = plt.figure(figsize=(6, 4))
	plt.barh(list(levels.keys()), impact, color='blue', height=20, zorder=2)
	plt.gca().set_xlabel(f'Impact of {var_type}')
	plt.gca().set_ylabel('Pressure Levels')
	plt.gca().yaxis.tick_right()
	plt.gca().invert_yaxis()
	plt.grid(True, color='gray', zorder=1)
	pdf.savefig()

pdf.close()
