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
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, submit_job, parse_config, wrf_version, Version

def run_wrfplus_ad(work_root, wrfplus_root, config, args):
	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)
	max_dom = config['domains']['max_dom']

	wrf_work_dir = os.path.abspath(work_root) + '/wrf'
	if not os.path.isdir(wrf_work_dir):
		cli.error(f'WRF work directory {wrf_work_dir} does not exist!')

	wrfplus_work_dir = os.path.abspath(work_root) + '/wrfplus'
	if not os.path.isdir(wrfplus_work_dir):
		cli.error(f'WRFPLUS has not been configured! Run config_wrfplus.py first.')
	os.chdir(wrfplus_work_dir)

	if os.path.isfile(f'{wrf_work_dir}/wrfinput_d01_{start_time_str}'):
		run(f'ln -sf {wrf_work_dir}/wrfinput_d01 .')
	elif os.path.isfile(f'{wrf_work_dir}/wrfout_d01_{start_time_str}'):
		run(f'ln -sf {wrf_work_dir}/wrfout_d01_{start_time_str} wrfinput_d01')
	run(f'ln -sf {wrf_work_dir}/wrfbdy_d01 .')
	if not os.path.isfile('final_sens_d01'):
		cli.error('There is no final_sens_d01 file!')

	version = wrf_version(wrfplus_root)

	cli.stage(f'Run WRFPLUS at {wrfplus_work_dir} ...')
	expected_files = ['wrfout_d{:02d}_{}'.format(i + 1, start_time_str) for i in range(max_dom)]
	expected_files.append(f'init_sens_d01_{start_time_str}')
	if not check_files(expected_files) or args.force:
		run('rm -f wrfout_*')
		try:
			run(f'ln -sf {wrfplus_root}/run/LANDUSE.TBL .')
			run(f'ln -sf {wrfplus_root}/run/VEGPARM.TBL .')
			run(f'ln -sf {wrfplus_root}/run/SOILPARM.TBL .')
			run(f'ln -sf {wrfplus_root}/run/GENPARM.TBL .')
			run(f'ln -sf {wrfplus_root}/run/RRTM_DATA_DBL RRTM_DATA')
			run(f'ln -sf {wrfplus_root}/run/ETAMPNEW_DATA_DBL ETAMPNEW_DATA')
			if version >= Version('4.0'):
				cmd = f'{wrfplus_root}/run/wrfplus.exe'
			else:
				cmd = f'{wrfplus_root}/run/wrf.exe'
			submit_job(cmd, args.np, config, args, wait=True)
		except KeyboardInterrupt:
			cli.warning('Ended by user!')
			proc.kill()
			sys.exit()
		if os.path.isfile(f'gradient_wrfplus_d01_{start_time_str}'):
			run(f'mv gradient_wrfplus_d01_{start_time_str} init_sens_d01_{start_time_str}')
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {os.path.abspath(wrfplus_work_dir)}/rsl.error.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File wrfout_* already exist.')
	run(f'ls -l {wrfplus_work_dir}/wrfout_*')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRFPLUS tangent and adjoint models.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrfplus-root', dest='wrfplus_root', help='WRFPLUS root directory (e.g. WRFPLUS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRFPLUS.', default=2, type=int)
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

	if not args.wrfplus_root:
		if os.getenv('WRFPLUS_ROOT'):
			args.wrfplus_root = os.getenv('WRFPLUS_ROOT')
		elif args.codes:
			args.wrfplus_root = args.codes + '/WRFPLUS'
		else:
			cli.error('Option --wrfplus-root or environment variable WRFPLUS_ROOT need to be set!')
	if not os.path.isdir(args.wrfplus_root):
		cli.error(f'Directory {args.wrfplus_root} does not exist!')
	
	config = parse_config(args.config_json)

	run_wrfplus_ad(args.work_root, args.wrfplus_root, config, args)
