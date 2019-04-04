#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import re
import sys
import config_wrfda
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

scripts_root = os.path.dirname(os.path.realpath(__file__))

def run_wrfda_3dvar(work_root, wrfda_root, config, args, wrf_work_dir=None):
	common_config = config['common']
	if not 'wrfda' in config:
		cli.error('There is no "wrfda" in configuration file!')
	wrfda_config = config['wrfda']
	
	start_time = common_config['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)

	if not wrf_work_dir: wrf_work_dir = os.path.abspath(work_root) + '/wrf'
	if not os.path.isdir(wrf_work_dir): cli.error(f'{wrf_work_dir} does not exist!')

	be_work_dir = os.path.abspath(work_root) + '/be'

	wrfda_work_dir = os.path.abspath(work_root) + '/wrfda'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	if os.path.isfile(f'wrfvar_output_{start_time_str}'):
		run(f'ls -l wrfvar_output_{start_time_str}')
		cli.notice(f'wrfvar_output_{start_time_str} already exist.')
		return

	run(f'ln -sf {wrfda_root}/run/LANDUSE.TBL {wrfda_work_dir}')

	if not os.path.isfile('namelist.input'):
		cli.error('namelist.input has not been generated! Run config_wrfda.py.')

	# BE matrix
	if 'cv_options' in wrfda_config:
		if wrfda_config['cv_options'] == 5:
			if not os.path.isdir(f'{be_work_dir}/be.dat.cv5'):
				cli.error(f'BE matrix {be_work_dir}/be.dat.cv5 does not exist!')
			run(f'ln -sf {be_work_dir}/be.dat.cv5 be.dat')
		elif wrfda_config['cv_options'] == 6:
			if not os.path.isdir(f'{be_work_dir}/be.dat.cv6'):
				cli.error(f'BE matrix {be_work_dir}/be.dat.cv6 does not exist!')
			run(f'ln -sf {be_work_dir}/be.dat.cv6 be.dat')
		elif wrfda_config['cv_options'] == 7:
			if not os.path.isdir(f'{be_work_dir}/be.dat.cv7'):
				cli.error(f'BE matrix {be_work_dir}/be.dat.cv7 does not exist!')
			run(f'ln -sf {be_work_dir}/be.dat.cv7 be.dat')
	if not os.path.exists('./be.dat'):
		run(f'ln -sf {wrfda_root}/var/run/be.dat.cv3 be.dat')

	# First guess
	expected_files = ['{}/wrfinput_d{:02d}_{}'.format(wrf_work_dir, i + 1, start_time_str) for i in range(common_config['max_dom'])]
	if not check_files(expected_files):
		cli.error('real.exe or da_update_bc.exe wasn\'t executed successfully!')
	# TODO: Assume there is only one domain to be assimilated.
	run(f'ln -sf {wrf_work_dir}/wrfinput_d01_{start_time_str} {wrfda_work_dir}/fg')

	# Observation data
	if wrfda_config['type'] == '3dvar' and wrfda_config['ob_format'] == 2 and os.path.isfile(f'obs_gts_{start_time.format(datetime_fmt)}.3DVAR'):
		run(f'ln -sf obs_gts_{start_time.format(datetime_fmt)}.3DVAR ob.ascii')
	if wrfda_config['ob_format'] == 1 and not os.path.isfile('ob.bufr'): cli.error('ob.bufr does not exist!')
	if wrfda_config['ob_format'] == 2 and not os.path.isfile('ob.ascii'): cli.error('ob.ascii does not exist!')

	if os.path.isfile(f'{wrfda_work_dir}/wrfvar_output_{start_time_str}') and not args.force:
		cli.notice(f'{wrfda_work_dir}/wrfvar_output_{start_time_str} already exists.')
		return

	run(f'{wrfda_root}/var/build/da_wrfvar.exe')

	expected_files = [f'wrfvar_output', 'statistics']
	if not check_files(expected_files):
		cli.error('Failed!')
	else:
		print(open('statistics').read())
		run(f'ncl -Q {scripts_root}/plots/plot_cost_grad_fn.ncl')
		run(f'cp wrfvar_output wrfvar_output_{start_time_str}')
		cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRFDA 3DVar system.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS, WRFDA)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')    
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument(      '--wrf-work-dir', dest='wrf_work_dir', help='Work directory of WRF')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or environment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wrfda_root = args.codes + '/WRFDA'
		else:
			cli.error('Option --wrfda-root or environment variable WRFDA_ROOT need to be set!')
	args.wrfda_root = os.path.abspath(args.wrfda_root)
	if not os.path.isdir(args.wrfda_root):
		cli.error(f'Directory {args.wrfda_root} does not exist!')

	if args.wrf_work_dir: args.wrf_work_dir = os.path.abspath(args.wrf_work_dir)

	config = parse_config(args.config_json)

	run_wrfda_3dvar(args.work_root, args.wrfda_root, config, args, args.wrf_work_dir)
