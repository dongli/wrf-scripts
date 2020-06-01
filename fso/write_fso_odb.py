#!/usr/bin/env python3

import argparse
import pendulum
import os
import re
import tempfile
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, parse_time, run

real_missing_value = -888888.0
int_missing_value = -88

parser = argparse.ArgumentParser(description='Write FSO results to ODB file.', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')
parser.add_argument('-t', '--datetime', help='Set the validating date time', type=parse_time)
parser.add_argument('-o', '--output-prefix', dest='output_prefix', help='Output prefix for ODB files')
args = parser.parse_args()

if not args.output_prefix:
	args.output_prefix = f'{args.work_root}/sens/wrfda/fso_result.odb'

obs_type_impact = {
	'synop'   : 0,
	'metar'   : 0,
	'ships'   : 0,
	'buoy'    : 0,
	'sondesfc': 0,
	'sound'   : 0,
	'profiler': 0,
	'airep'   : 0,
	'pilot'   : 0,
	'qscat'   : 0
}
var_type_impact = {
	'u': 0,
	'v': 0,
	't': 0,
	'q': 0,
	'p': 0
}

gts_omb_oma_01 = open(f'{args.work_root}/sens/wrfda/gts_omb_oma_01', 'r')

header = ''
header += 'obs_type@detail_impact:STRING\t'
header += 'sid@detail_impact:STRING\t'
header += 'lon@detail_impact:REAL\t'
header += 'lat@detail_impact:REAL\t'
header += 'date@detail_impact:INTEGER\t'
header += 'time@detail_impact:INTEGER\t'
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
	if x.strip() == '' or float(x) == real_missing_value: x = 'NULL'
	return x

def handle_int_missing_value(x):
	if x.strip() == '' or int(x) == int_missing_value: x = 'NULL'
	return x

while True:
	line = gts_omb_oma_01.readline()
	if re.match('^\s*\w+\s+\d+$', line):
		obs_type, num_platform = [x.strip() for x in line.split()]
		if obs_type == 'sonde_sfc': obs_type = 'sondesfc'
		num_platform = int(num_platform)
		print(obs_type, num_platform)
		for i in range(num_platform):
			pos = gts_omb_oma_01.tell()
			line = gts_omb_oma_01.readline()
			try:
				n = int(line.strip())
			except:
				gts_omb_oma_01.seek(pos)
				break
			for j in range(n):
				pos = gts_omb_oma_01.tell()
				line = gts_omb_oma_01.readline()
				if len(line) < 10:
					gts_omb_oma_01.seek(pos)
					break
				k = 16
				try:
					sid      =                           line[k:k+6 ] ; k += 6
					lat      = handle_real_missing_value(line[k:k+9 ]); k += 9
					lon      = handle_real_missing_value(line[k:k+9 ]); k += 9
					p        = handle_real_missing_value(line[k:k+17]); k += 17
					u        = handle_real_missing_value(line[k:k+17]); k += 17
					u_impact = handle_real_missing_value(line[k:k+17]); k += 17
					u_qc     = handle_int_missing_value (line[k:k+8 ]); k += 8
					u_obserr = handle_real_missing_value(line[k:k+17]); k += 17
					u_incr   = handle_real_missing_value(line[k:k+17]); k += 17
					v        = handle_real_missing_value(line[k:k+17]); k += 17
					v_impact = handle_real_missing_value(line[k:k+17]); k += 17
					v_qc     = handle_int_missing_value (line[k:k+8 ]); k += 8
					v_obserr = handle_real_missing_value(line[k:k+17]); k += 17
					v_incr   = handle_real_missing_value(line[k:k+17]); k += 17
					t        = handle_real_missing_value(line[k:k+17]); k += 17
					t_impact = handle_real_missing_value(line[k:k+17]); k += 17
					t_qc     = handle_int_missing_value (line[k:k+8 ]); k += 8
					t_obserr = handle_real_missing_value(line[k:k+17]); k += 17
					t_incr   = handle_real_missing_value(line[k:k+17]); k += 17
					if obs_type in ('synop', 'metar', 'ships', 'buoy', 'sondesfc'):
						p        = handle_real_missing_value(line[k:k+17]); k += 17
						p_impact = handle_real_missing_value(line[k:k+17]); k += 17
						p_qc     = handle_int_missing_value (line[k:k+8 ]); k += 8
						p_obserr = handle_real_missing_value(line[k:k+17]); k += 17
						p_incr   = handle_real_missing_value(line[k:k+17]); k += 17
					elif obs_type in ('sound', 'airep', 'profiler', 'pilot', 'qscat'):
						p_impact = 'NULL'
						p_qc     = 'NULL'
						p_obserr = 'NULL'
						p_incr   = 'NULL'
					else:
						cli.error(f'Unsupported obs_type {obs_type}!')
					q        = handle_real_missing_value(line[k:k+17]); k += 17 
					q_impact = handle_real_missing_value(line[k:k+17]); k += 17
					q_qc     = handle_int_missing_value (line[k:k+8 ]); k += 8
					q_obserr = handle_real_missing_value(line[k:k+17]); k += 17
					q_incr   = handle_real_missing_value(line[k:k+17]); k += 17
				except Exception as e:
					print(line)
					print(e)
					cli.error('Failed to parse line!')

				# Accumulate impacts of different observation and variable types.
				if obs_type in ('synop', 'metar', 'ships', 'buoy', 'sondesfc'):
					obs_type_impact[obs_type] = obs_type_impact[obs_type] + float(u_impact) + float(v_impact) + float(t_impact) + float(q_impact) + float(p_impact)
					var_type_impact['u'] = var_type_impact['u'] + float(u_impact)
					var_type_impact['v'] = var_type_impact['v'] + float(v_impact)
					var_type_impact['t'] = var_type_impact['t'] + float(t_impact)
					var_type_impact['q'] = var_type_impact['q'] + float(q_impact)
					var_type_impact['p'] = var_type_impact['p'] + float(p_impact)
				elif obs_type in ('sound', 'airep'):
					obs_type_impact[obs_type] = obs_type_impact[obs_type] + float(u_impact) + float(v_impact) + float(t_impact) + float(q_impact)
					var_type_impact['u'] = var_type_impact['u'] + float(u_impact)
					var_type_impact['v'] = var_type_impact['v'] + float(v_impact)
					var_type_impact['t'] = var_type_impact['t'] + float(t_impact)
					var_type_impact['q'] = var_type_impact['q'] + float(q_impact)
				elif obs_type in ('profiler', 'pilot', 'qscat'):
					obs_type_impact[obs_type] = obs_type_impact[obs_type] + float(u_impact) + float(v_impact)
					var_type_impact['u'] = var_type_impact['u'] + float(u_impact)
					var_type_impact['v'] = var_type_impact['v'] + float(v_impact)

				# Write output to tempfile.
				output.write(obs_type + '\t')
				output.write(sid      + '\t')
				output.write(lon      + '\t')
				output.write(lat      + '\t')
				if args.datetime:
					output.write(args.datetime.format('YYYYMMDD') + '\t')
					output.write(args.datetime.format('HHmmss') + '\t')
				else:
					output.write('NULL\t')
					output.write('NULL\t')
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
	else:
		break

output.flush()
cli.notice(f'Write {args.output_prefix}.detail_impact.')
run(f'odb import -d TAB {output.name} {args.output_prefix}.detail_impact', stdout=True)

# Impacts per observation types
header = ''
header += 'obs_type@fso_obs_impact:STRING\t'
header += 'obs_impact@fso_obs_impact:REAL\n'

output = tempfile.NamedTemporaryFile(mode='w')
output.write(header)

for obs_type, impact in obs_type_impact.items():
	output.write(f'{obs_type}\t{impact}\n')

output.flush()
cli.notice(f'Write {args.output_prefix}.obs_impact.')
run(f'odb import -d TAB {output.name} {args.output_prefix}.obs_impact', stdout=True)

# Impacts per variable types.
header = ''
header += 'var_type@fso_var_impact:STRING\t'
header += 'var_impact@fso_var_impact:REAL\n'

output = tempfile.NamedTemporaryFile(mode='w')
output.write(header)

for var_type, impact in var_type_impact.items():
	output.write(f'{var_type}\t{impact}\n')

output.flush()
cli.notice(f'Write {args.output_prefix}.var_impact.')
run(f'odb import -d TAB {output.name} {args.output_prefix}.var_impact', stdout=True)

