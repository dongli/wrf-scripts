#! /usr/bin/env python3

import argparse
from glob import glob
import os
import f90nml
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, check_files, run, parse_config, submit_job

def run_wrfda_update_bc(work_root, wrfda_root, update_lowbc, config, args, wrf_work_dir=None, tag=None):
	start_time = config['custom']['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)
	max_dom = config['domains']['max_dom']

	if not wrf_work_dir:
		if tag != None:
			wrf_work_dir = f'{work_root}/wrf_{tag}'
		else:
			wrf_work_dir = f'{work_root}/wrf'

	if max_dom > 1:
		dom_str = 'd' + str(config['custom']['wrfda']['dom'] + 1).zfill(2)
		if tag != None:
			wrfda_work_dir = f'{work_root}/wrfda_{tag}/{dom_str}'
		else:
			wrfda_work_dir = f'{work_root}/wrfda/{dom_str}'
	else:
		dom_str = 'd01'
		if tag != None:
			wrfda_work_dir = f'{work_root}/wrfda_{tag}'
		else:
			wrfda_work_dir = f'{work_root}/wrfda'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	cli.stage(f'Run WRFDA update_bc at {wrfda_work_dir} ...')

	expected_files = [f'{wrf_work_dir}/wrfbdy_{dom_str}_{start_time_str}', f'wrfvar_output_{start_time_str}', 'fg']
	if not check_files(expected_files):
		cli.error('da_wrfvar.exe or real.exe wasn\'t executed successfully!')
	run(f'cp {wrf_work_dir}/wrfbdy_{dom_str}_{start_time_str} wrfbdy_{dom_str}')
	run(f'cp wrfvar_output_{start_time_str} wrfvar_output')

	parame_in = f90nml.read(f'{wrfda_root}/var/test/update_bc/parame.in')
	parame_in['control_param']['wrf_input'] = './fg'
	if update_lowbc:
		cli.notice('Update only low boundary condition.')
		parame_in['control_param']['low_bdy_only'] = True
	parame_in.write(f'{wrfda_work_dir}/parame.in', force=True)

	if update_lowbc:
		expected_file = f'wrfbdy_{dom_str}_{start_time_str}.low_updated'
	else:
		expected_file = f'wrfbdy_{dom_str}_{start_time_str}.lateral_updated'
	if not check_files(expected_file) or args.force:
		submit_job(f'{wrfda_root}/var/build/da_update_bc.exe', args.np, config, args, wait=True)
		run(f'cp wrfbdy_{dom_str} {expected_file}')
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
	parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs.', action='store_true')
	parser.add_argument(      '--pbs', help='Use PBS job management system variants (e.g. TORQUE) to run MPI jobs.', action='store_true')
	parser.add_argument(      '--ntasks-per-node', dest='ntasks_per_node', help='Override the default setting.', default=None, type=int)
	parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
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
