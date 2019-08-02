#!/usr/bin/env python3

import argparse
import pendulum
import os
import re
from subprocess import run, PIPE
import tempfile

real_missing_value = -888888.0
int_missing_value = -88

parser = argparse.ArgumentParser(description='Write FSO results to ODB file.', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')
parser.add_argument('-o', '--output-prefix', dest='output_prefix', help='Output prefix for ODB files')
args = parser.parse_args()

if not args.output_prefix:
	args.output_prefix = f'{args.work_root}/sens/wrfda/fso_result.odb'

rsl_out = open(f'{args.work_root}/sens/wrfda/rsl.out.0000', 'r')
lines = ''.join(rsl_out.readlines())

header = ''
header += 'obs_type@fso_obs_impact:STRING\t'
header += 'obs_impact@fso_obs_impact:REAL\n'

output = tempfile.NamedTemporaryFile(mode='w')
output.write(header)

for obs_type in ('sound', 'synop', 'pilot', 'satem', 'geoamv', 'polaramv', 'airep', 'gpspw', 'gpsrf', 'metar', 'ships', 'ssmi_rv', 'qscat', 'profiler', 'buoy', 'bogus', 'pseudo', 'mtgirs', 'tamdar'):
	match = re.search(f'\s*{obs_type}\s+([-+]?\d+\.\d+E[-+]?\d+)', lines)
	if match:
		output.write(f'{obs_type}\t{match[1]}\n')

output.flush()
print(f'[Notice]: Write {args.output_prefix}.obs_impact.')
res = run(f'odb import -d TAB {output.name} {args.output_prefix}.obs_impact', shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print(res.stderr.decode('utf-8'))

header = ''
header += 'var_type@fso_var_impact:STRING\t'
header += 'var_impact@fso_var_impact:REAL\n'

output = tempfile.NamedTemporaryFile(mode='w')
output.write(header)

for var_type in ('u', 'v', 't', 'p', 'q'):
	match = re.search(f'\s*{var_type}\s+([-+]?\d+\.\d+E[-+]?\d+)', lines, re.I)
	if match:
		output.write(f'{var_type}\t{match[1]}\n')

output.flush()
print(f'[Notice]: Write {args.output_prefix}.var_impact.')
res = run(f'odb import -d TAB {output.name} {args.output_prefix}.var_impact', shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print(res.stderr.decode('utf-8'))

gts_omb_oma_01 = open(f'{args.work_root}/sens/wrfda/gts_omb_oma_01', 'r')

header = ''
header += 'obs_type@detail_impact:STRING\t'
header += 'lon@detail_impact:REAL\t'
header += 'lat@detail_impact:REAL\t'
header += 'u@detail_impact:REAL\t'
header += 'u_impact@detail_impact:REAL\t'
header += 'u_qc@detail_impact:INTEGER\t'
header += 'u_obserr@detail_impact:REAL\t'
header += 'u_incr@detail_impact:REAL\t'
header += 'v@detail_impact:REAL\t'
header += 'v_impact@detail_impact:REAL\t'
header += 'v_qc@detail_impact:INTEGER\t'
header += 'v_obserr@detail_impact:REAL\t'
header += 'v_incr@detail_impact:REAL\t'
header += 't@detail_impact:REAL\t'
header += 't_impact@detail_impact:REAL\t'
header += 't_qc@detail_impact:INTEGER\t'
header += 't_obserr@detail_impact:REAL\t'
header += 't_incr@detail_impact:REAL\t'
header += 'p@detail_impact:REAL\t'
header += 'p_impact@detail_impact:REAL\t'
header += 'p_qc@detail_impact:INTEGER\t'
header += 'p_obserr@detail_impact:REAL\t'
header += 'p_incr@detail_impact:REAL\t'
header += 'q@detail_impact:REAL\t'
header += 'q_impact@detail_impact:REAL\t'
header += 'q_qc@detail_impact:INTEGER\t'
header += 'q_obserr@detail_impact:REAL\t'
header += 'q_incr@detail_impact:REAL\n'

output = tempfile.NamedTemporaryFile(mode='w')
output.write(header)

def handle_real_missing_value(x):
	if float(x) == real_missing_value: x = 'NULL'
	return x

def handle_int_missing_value(x):
	if int(x) == int_missing_value: x = 'NULL'
	return x

while True:
	line = gts_omb_oma_01.readline()
	if re.match('^\s*\w+\s+\d+$', line):
		obs_type, num_platform = [x.strip() for x in line.split()]
		if obs_type == 'sonde_sfc': obs_type = 'sondesfc'
		num_platform = int(num_platform)
		print(obs_type, num_platform)
		for i in range(num_platform):
			line = gts_omb_oma_01.readline()
			n = int(line.strip())
			for j in range(n):
				line = gts_omb_oma_01.readline()
				tmp = [x.strip() for x in line.split()]
				k = 2
				lat      = handle_real_missing_value(tmp[k]); k += 1
				lon      = handle_real_missing_value(tmp[k]); k += 1 
				p        = handle_real_missing_value(tmp[k]); k += 1 
				u        = handle_real_missing_value(tmp[k]); k += 1 
				u_impact = handle_real_missing_value(tmp[k]); k += 1 
				u_qc     = handle_int_missing_value (tmp[k]); k += 1 
				u_obserr = handle_real_missing_value(tmp[k]); k += 1 
				u_incr   = handle_real_missing_value(tmp[k]); k += 1 
				v        = handle_real_missing_value(tmp[k]); k += 1 
				v_impact = handle_real_missing_value(tmp[k]); k += 1 
				v_qc     = handle_int_missing_value (tmp[k]); k += 1 
				v_obserr = handle_real_missing_value(tmp[k]); k += 1 
				v_incr   = handle_real_missing_value(tmp[k]); k += 1 
				t        = handle_real_missing_value(tmp[k]); k += 1 
				t_impact = handle_real_missing_value(tmp[k]); k += 1 
				t_qc     = handle_int_missing_value (tmp[k]); k += 1 
				t_obserr = handle_real_missing_value(tmp[k]); k += 1 
				t_incr   = handle_real_missing_value(tmp[k]); k += 1 
				if obs_type in ('synop', 'metar', 'ships', 'buoy', 'sondesfc'):
					p        = handle_real_missing_value(tmp[k]); k += 1 
					p_impact = handle_real_missing_value(tmp[k]); k += 1 
					p_qc     = handle_int_missing_value (tmp[k]); k += 1 
					p_obserr = handle_real_missing_value(tmp[k]); k += 1 
					p_incr   = handle_real_missing_value(tmp[k]); k += 1 
				elif obs_type in ('sound', 'airep'):
					p_impact = 'NULL'
					p_qc     = 'NULL'
					p_obserr = 'NULL'
					p_incr   = 'NULL'
				else:
					print(f'[Error]: Unsupported obs_type {obs_type}!')
				q        = handle_real_missing_value(tmp[k]); k += 1 
				q_impact = handle_real_missing_value(tmp[k]); k += 1 
				q_qc     = handle_int_missing_value (tmp[k]); k += 1 
				q_obserr = handle_real_missing_value(tmp[k]); k += 1 
				q_incr   = handle_real_missing_value(tmp[k]); k += 1 

				# Write output to tempfile.
				output.write(obs_type + '\t')
				output.write(lon      + '\t')
				output.write(lat      + '\t')
				output.write(u        + '\t')
				output.write(u_impact + '\t')
				output.write(u_qc     + '\t')
				output.write(u_obserr + '\t')
				output.write(u_incr   + '\t')
				output.write(v        + '\t')
				output.write(v_impact + '\t')
				output.write(v_qc     + '\t')
				output.write(v_obserr + '\t')
				output.write(v_incr   + '\t')
				output.write(t        + '\t')
				output.write(t_impact + '\t')
				output.write(t_qc     + '\t')
				output.write(t_obserr + '\t')
				output.write(t_incr   + '\t')
				output.write(p        + '\t')
				output.write(p_impact + '\t')
				output.write(p_qc     + '\t')
				output.write(p_obserr + '\t')
				output.write(p_incr   + '\t')
				output.write(q        + '\t')
				output.write(q_impact + '\t')
				output.write(q_qc     + '\t')
				output.write(q_obserr + '\t')
				output.write(q_incr   + '\t')
				output.write('\n')
	else:
		break

output.flush()
print(f'[Notice]: Write {args.output_prefix}.detail_impact.')
res = run(f'odb import -d TAB {output.name} {args.output_prefix}.detail_impact', shell=True, stdout=PIPE, stderr=PIPE)
if res.returncode != 0:
	print(res.stderr.decode('utf-8'))
