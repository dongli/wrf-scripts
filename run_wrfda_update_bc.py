#! /usr/bin/env python3

import argparse
from glob import glob
import os
import f90nml
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wrfda_update_bc(work_root, wrfda_root, update_lowbc, config, args):
	common_config = config['common']

	start_time = common_config['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)

	wrf_work_dir = os.path.abspath(work_root) + '/wrf'

	wrfda_work_dir = os.path.abspath(work_root) + '/wrfda'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)


	expected_files = [f'{wrf_work_dir}/wrfbdy_d01_{start_time_str}', f'wrfvar_output_{start_time_str}', 'fg']
	if not check_files(expected_files):
		cli.error('da_wrfvar.exe or real.exe wasn\'t executed successfully!')
	run(f'cp {wrf_work_dir}/wrfbdy_d01_{start_time_str} wrfbdy_d01')
	run(f'cp wrfvar_output_{start_time_str} wrfvar_output')

	parame_in = f90nml.read(f'{wrfda_root}/var/test/update_bc/parame.in')
	parame_in['control_param']['wrf_input'] = './fg'
	if update_lowbc:
		cli.notice('Update only low boundary condition.')
		parame_in['control_param']['low_bdy_only'] = True
	parame_in.write(f'{wrfda_work_dir}/parame.in', force=True)

	cli.stage(f'Run WRFDA update_bc at {wrfda_work_dir} ...')
	if update_lowbc:
		expected_file = f'wrfbdy_d01_{start_time_str}.low_updated'
	else:
		expected_file = f'wrfbdy_d01_{start_time_str}.lateral_updated'
	if not check_files(expected_file) or args.force:
		if args.verbose:
			run(f'{wrfda_root}/var/build/da_update_bc.exe')
		else:
			run(f'{wrfda_root}/var/build/da_update_bc.exe &> da_update_bc.out')
		run(f'cp wrfbdy_d01 {expected_file}')
	else:
		run(f'ls -l {expected_file}')

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRFDA update_bc tool.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
	parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')	
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-l', '--update-lowbc', dest='update_lowbc', help='Update low boundary condition.', action='store_true')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.wrfda_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or enviroment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wrfda_root = args.codes + '/WRFDA'
		else:
			cli.error('Option --wrfda-root or enviroment variable WRFDA_ROOT need to be set!')
	args.wrfda_root = os.path.abspath(args.wrfda_root)
	if not os.path.isdir(args.wrfda_root):
		cli.error(f'Directory {args.wrfda_root} does not exist!')

	config = parse_config(args.config_json)

	run_wrfda_update_bc(args.work_root, args.wrfda_root, args.update_lowbc, config, args)
