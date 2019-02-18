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

def check_wrfout_times(wrfout_file_paths, start_time):
	for wrfout_file_path in wrfout_file_paths:
		if wrfout_file_path[0:6] != 'wrfout': continue
		wrfout = Dataset(wrfout_file_path)
		try:
			if wrfout.variables['Times'][0].tobytes().decode('utf-8') != start_time.format('YYYY-MM-DD_HH:mm:ss') or wrfout.variables['Times'][-1].tobytes().decode('utf-8') != start_time.format('YYYY-MM-DD_HH:mm:ss') or wrfout.variables['Times'].shape[0] <= 1:
				wrfout.close()
				return False
		except Exception as e:
			print(e)
			wrfout.close()
			return False
		wrfout.close()
	return True

def run_wrfplus_ad(work_root, wrfplus_root, config, args):
	common_config = config['common']

	start_time = common_config['start_time']
	end_time = common_config['end_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)

	wrf_work_dir = os.path.abspath(work_root) + '/wrf'
	if not os.path.isdir(wrf_work_dir):
		cli.error(f'WRF work directory {wrf_work_dir} does not exist!')

	wrfplus_work_dir = os.path.abspath(work_root) + '/wrfplus'
	if not os.path.isdir(wrfplus_work_dir):
		cli.error(f'WRFPLUS has not been configured! Run config_wrfplus.py first.')
	os.chdir(wrfplus_work_dir)

	if os.path.isfile(f'{wrf_work_dir}/wrfinput_d01'):
		run(f'ln -sf {wrf_work_dir}/wrfinput_d01 .')
		run(f'ln -sf {wrf_work_dir}/wrfbdy_d01 .')
	if not os.path.isfile('final_sens_d01'):
		cli.error('There is no final_sens_d01 file!')

	expected_files = ['wrfout_d{:02d}_{}'.format(i + 1, start_time_str) for i in range(common_config['max_dom'])]
	expected_files.append(f'init_sens_d01_{start_time_str}')
	if not check_files(expected_files) or not check_wrfout_times(expected_files, start_time) or args.force:
		run('rm -f wrfout_*')
		try:
			run(f'ln -sf {wrfplus_root}/run/LANDUSE.TBL .')
			run(f'ln -sf {wrfplus_root}/run/VEGPARM.TBL .')
			run(f'ln -sf {wrfplus_root}/run/SOILPARM.TBL .')
			run(f'ln -sf {wrfplus_root}/run/GENPARM.TBL .')
			run(f'ln -sf {wrfplus_root}/run/RRTM_DATA_DBL RRTM_DATA')
			run(f'ln -sf {wrfplus_root}/run/ETAMPNEW_DATA_DBL ETAMPNEW_DATA')
			proc = run(f'mpiexec -np {args.np} {wrfplus_root}/run/wrfplus.exe', bg=True)
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
		if os.path.isfile(f'gradient_wrfplus_d01_{start_time_str}'):
			run(f'mv gradient_wrfplus_d01_{start_time_str} init_sens_d01_{start_time_str}')
		if not check_files(expected_files) or not check_wrfout_times(expected_files, start_time):
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
