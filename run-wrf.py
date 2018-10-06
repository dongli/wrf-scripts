#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import re
from shutil import copyfile
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config, edit_file

parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
parser.add_argument('-f', '--force', help='Force to run', action='store_true')
args = parser.parse_args()

if not args.wrf_root:
	if os.getenv('WRF_ROOT'):
		args.wrf_root = os.getenv('WRF_ROOT')
	elif args.codes:
		args.wrf_root = args.codes + '/WRF'
	else:
		cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')

if not args.wps_root:
	if os.getenv('WPS_ROOT'):
		args.wps_root = os.getenv('WPS_ROOT')
	elif args.codes:
		args.wps_root = args.codes + '/WPS'
	else:
		cli.error('Option --wps-root or environment variable WPS_ROOT need to be set!')

args.wps_root = os.path.abspath(args.wps_root)
if not os.path.isdir(args.wps_root):
	cli.error(f'Directory {args.wps_root} does not exist!')

config = parse_config(args.config_json)
common_config = config['common']

# Shortcuts
start_time = common_config['start_time']
end_time = common_config['end_time']

time_format_str = 'YYYY-MM-DD_HH:mm:ss'

os.chdir(args.wrf_root + '/run')

expected_files = ['wrfinput_d{:02d}'.format(i + 1) for i in range(common_config['max_dom'])]
expected_files.append('wrfbdy_d01')
if not check_files(expected_files):
	cli.error('real.exe wasn\'t executed successfully!')

expected_files = ['wrfout_d{:02d}:{}'.format(i + 1, end_time.format(time_format_str)) for i in range(common_config['max_dom'])]
if not check_files(expected_files) or args.force:
	run('rm -f wrfout_*')
	run(f'mpiexec -np {args.np} ./wrf.exe')
	if not check_files(expected_files):
		cli.error(f'Failed! Check output {os.path.abspath(args.wrf_root)}/run/rsl.error.0000.')
	cli.notice('Succeeded.')
else:
	cli.notice('File wrfout_* already exist.')
run(f'ls -l {args.wrf_root}/run/wrfout_*')
