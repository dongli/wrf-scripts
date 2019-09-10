#!/usr/bin/env python3

import argparse
from glob import glob
import os
import re
import pendulum
import subprocess
from time import sleep
from shutil import copyfile
from netCDF4 import Dataset
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, check_files, run, submit_job, parse_config

def copy_wrfda_output(dom_str, start_time_str, wrfda_work_dir):
	if os.path.isfile(f'{wrfda_work_dir}/wrfvar_output_{start_time_str}'):
		cli.notice(f'Use assimilated input for domain {dom_str}.')
	else:
		return False
	run(f'ln -sf {wrfda_work_dir}/wrfvar_output_{start_time_str} wrfinput_{dom_str}')
	if dom_str == 'd01':
		run(f'ln -sf {wrfda_work_dir}/wrfbdy_d01_{start_time_str}.lateral_updated wrfbdy_d01')
	return True

def run_wrf(work_root, wrf_root, config, args):
	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)
	end_time_str = end_time.format(datetime_fmt)
	max_dom = config['domains']['max_dom']

	wrfda_work_dir = os.path.abspath(work_root) + '/wrfda'

	wrf_work_dir = os.path.abspath(work_root) + '/wrf'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	all_wrfda_ok = True
	for dom_idx in range(max_dom):
		dom_str = 'd' + str(dom_idx + 1).zfill(2)
		if not copy_wrfda_output(dom_str, start_time_str, wrfda_work_dir + '/' + dom_str):
			all_wrfda_ok = False
			break
	if not all_wrfda_ok:
		cli.warning('Do not use data assimilation.')
		expected_files = ['wrfinput_d{:02d}_{}'.format(i + 1, start_time_str) for i in range(max_dom)]
		expected_files.append(f'wrfbdy_d01_{start_time_str}')
		if not check_files(expected_files):
			cli.error('real.exe wasn\'t executed successfully!')
		for i in range(max_dom):
			run('ln -sf wrfinput_d{0:02d}_{1} wrfinput_d{0:02d}'.format(i + 1, start_time_str))
		run(f'ln -sf wrfbdy_d01_{start_time_str} wrfbdy_d01')

	cli.stage(f'Run wrf.exe at {wrf_work_dir} ...')
	expected_files = ['wrfout_d{:02d}_{}'.format(i + 1, end_time_str) for i in range(max_dom)]
	if not check_files(expected_files) or args.force:
		run('rm -f wrfout_*')
		run(f'ln -sf {wrf_root}/run/LANDUSE.TBL .')
		run(f'ln -sf {wrf_root}/run/ozone_plev.formatted .')
		run(f'ln -sf {wrf_root}/run/ozone_lat.formatted .')
		run(f'ln -sf {wrf_root}/run/ozone.formatted .')
		run(f'ln -sf {wrf_root}/run/RRTM_DATA_DBL RRTM_DATA')
		run(f'ln -sf {wrf_root}/run/RRTMG_LW_DATA .')
		run(f'ln -sf {wrf_root}/run/RRTMG_SW_DATA .')
		run(f'ln -sf {wrf_root}/run/VEGPARM.TBL .')
		run(f'ln -sf {wrf_root}/run/SOILPARM.TBL .')
		run(f'ln -sf {wrf_root}/run/GENPARM.TBL .')
		submit_job(f'{wrf_root}/run/wrf.exe', args.np, config, args, wait=True)
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {os.path.abspath(wrf_work_dir)}/rsl.error.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File wrfout_* already exist.')
	run(f'ls -l {wrf_work_dir}/wrfout_*')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs.', action='store_true')
	parser.add_argument(      '--pbs', help='Use PBS job management system variants (e.g. TORQUE) to run MPI jobs.', action='store_true')
	parser.add_argument(      '--ntasks-per-node', dest='ntasks_per_node', help='Override the default setting.', default=None, type=int)
	parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or environment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

	if not args.wrf_root:
		if os.getenv('WRF_ROOT'):
			args.wrf_root = os.getenv('WRF_ROOT')
		elif args.codes:
			args.wrf_root = args.codes + '/WRF'
		else:
			cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')
	if not os.path.isdir(args.wrf_root):
		cli.error(f'Directory {args.wrf_root} does not exist!')
	
	config = parse_config(args.config_json)

	run_wrf(args.work_root, args.wrf_root, config, args)
