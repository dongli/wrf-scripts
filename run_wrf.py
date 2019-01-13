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
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wrf(work_root, wrf_root, wps_root, config, args):
	common_config = config['common']

	# Shortcuts
	start_time = common_config['start_time']
	end_time = common_config['end_time']

	wrf_work_dir = os.path.abspath(work_root) + '/WRF'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	expected_files = ['wrfinput_d{:02d}'.format(i + 1) for i in range(common_config['max_dom'])]
	expected_files.append('wrfbdy_d01')
	if not check_files(expected_files):
		cli.error('real.exe wasn\'t executed successfully!')

	expected_files = ['wrfout_d{:02d}_{}'.format(i + 1, end_time.format('YYYY-MM-DD_HH:mm:ss')) for i in range(common_config['max_dom'])]
	if not check_files(expected_files) or args.force:
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
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {os.path.abspath(wrf_work_dir)}/rsl.error.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File wrfout_* already exist.')
	run(f'ls -l {wrf_work_dir}/wrfout_*')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-r', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
	parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
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

	run_wrf(args.work_root, args.wrf_root, args.wps_root, config, args)
