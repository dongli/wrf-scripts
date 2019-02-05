#!/usr/bin/env python3

import argparse
from glob import glob
import os
import re
import pendulum
from progressbar import ProgressBar, Percentage, Bar, Timer
import subprocess
from time import sleep
from shutil import copyfile
from netCDF4 import Dataset
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def check_wrfout_times(expected_files, end_time):
	for expected_file in expected_files:
		wrfout = Dataset(expected_file)
		try:
			if wrfout.variables['Times'][-1].tobytes().decode('utf-8') != end_time.format('YYYY-MM-DD_HH:mm:ss'):
				return False
		except Exception as e:
			print(e)
			return False
	return True

def run_wrf(work_root, prod_root, wrf_root, config, args):
	common_config = config['common']

	start_time = common_config['start_time']
	end_time = common_config['end_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)

	wrf_work_dir = os.path.abspath(work_root) + '/WRF'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	if os.path.isfile(f'{prod_root}/wrfvar_output_{start_time_str}'):
		cli.notice('Use assimilated input for domain 01.')
		run(f'cp {prod_root}/wrfvar_output_{start_time_str} {wrf_work_dir}/wrfinput_d01')
		run(f'cp {prod_root}/wrfbdy_d01_{start_time_str}.lateral_updated {wrf_work_dir}/wrfbdy_d01')

	expected_files = ['wrfinput_d{:02d}'.format(i + 1) for i in range(common_config['max_dom'])]
	expected_files.append('wrfbdy_d01')
	if not check_files(expected_files):
		cli.error('real.exe wasn\'t executed successfully!')

	expected_files = ['wrfout_d{:02d}_{}'.format(i + 1, start_time_str) for i in range(common_config['max_dom'])]
	if not check_files(expected_files) or not check_wrfout_times(expected_files, end_time) or args.force:
		run('rm -f wrfout_*')
		try:
			run(f'ln -sf {wrf_root}/run/LANDUSE.TBL .')
			run(f'ln -sf {wrf_root}/run/ozone_plev.formatted .')
			run(f'ln -sf {wrf_root}/run/ozone_lat.formatted .')
			run(f'ln -sf {wrf_root}/run/ozone.formatted .')
			run(f'ln -sf {wrf_root}/run/RRTMG_LW_DATA .')
			run(f'ln -sf {wrf_root}/run/RRTMG_SW_DATA .')
			run(f'ln -sf {wrf_root}/run/VEGPARM.TBL .')
			run(f'ln -sf {wrf_root}/run/SOILPARM.TBL .')
			run(f'ln -sf {wrf_root}/run/GENPARM.TBL .')
			proc = run(f'mpiexec -np {args.np} {wrf_root}/run/wrf.exe', bg=True)
			bar = ProgressBar(max_value=100, widgets=[Percentage(), Bar(), Timer()])
			while proc.poll() == None:
				sleep(10)
				res = subprocess.run(['tail', '-n', '3', 'rsl.error.0000'], stdout=subprocess.PIPE)
				for line in res.stdout.decode('utf-8').split():
					time_match = re.match(r'(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})', line)
					if time_match:
						run_time = pendulum.from_format(time_match[0], 'YYYY-MM-DD_HH:mm:ss')
						run_progress = ((run_time - start_time).in_hours() / (end_time - start_time).in_hours()) * 100
						bar.update(int(run_progress))
						break
		except KeyboardInterrupt:
			cli.warning('Ended by user!')
			proc.kill()
			sys.exit()
		if not check_files(expected_files) or not check_wrfout_times(expected_files, end_time):
			cli.error(f'Failed! Check output {os.path.abspath(wrf_work_dir)}/rsl.error.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File wrfout_* already exist.')
	run(f'ls -l {wrf_work_dir}/wrfout_*')
	run(f'cp {wrf_work_dir}/wrfout_* {prod_root}')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-p', '--prod-root', dest='prod_root', help='Product root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
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

	if not args.prod_root:
		if os.getenv('PROD_ROOT'):
			args.work_root = os.getenv('PROD_ROOT')
		else:
			cli.error('Option --prod-root or environment variable PROD_ROOT need to be set!')
	args.prod_root = os.path.abspath(args.prod_root)
	if not os.path.isdir(args.prod_root):
		cli.error(f'Directory {args.prod_root} does not exist!')

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

	run_wrf(args.work_root, args.prod_root, args.wrf_root, config, args)
