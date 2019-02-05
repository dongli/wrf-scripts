#! /usr/bin/env python3

import argparse
from glob import glob
import os
import f90nml
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wrfda_update_bc(work_root, prod_root, wrfda_root, config, args):
	common_config = config['common']

	wrfda_work_dir = os.path.abspath(work_root) + '/WRFDA'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	run(f'ln -sf {wrfda_root}/var/build/da_update_bc.exe .')

	expected_files = [f'{prod_root}/wrfbdy_d01']
	if not check_files(expected_files):
		cli.error('da_wrfvar.exe or real.exe wasn\'t executed successfully!')
	for infile in expected_files:
		run(f'cp {infile} .')

	parame_in = f90nml.read(f'{wrfda_root}/var/test/update_bc/parame.in')
	parame_in['control_param']['wrf_input'] = './fg'
	parame_in.write(f'{wrfda_work_dir}/parame.in', force=True)

	if args.verbose:
		run('./da_update_bc.exe')
	else:
		run('./da_update_bc.exe &> da_update_bc.out')

	run(f'cp wrfbdy_d01 {prod_root}')

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')	
	parser.add_argument('-p', '--prod-root', dest='prod_root', help='Product root directory (e.g. gfs)')
	parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
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

	if not args.prod_root:
		if os.getenv('PROD_ROOT'):
			args.wrfda_root = os.getenv('PROD_ROOT')
		else:
			cli.error('Option --prod-root or enviroment variable PROD_ROOT need to be set!')
	args.prod_root = os.path.abspath(args.prod_root)
	if not os.path.isdir(args.prod_root):
		cli.error(f'Directory {args.prod_root} does not exist!')

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

	run_wrfda_update_bc(args.work_root, args.prod_root, args.wrfda_root, config, args)
