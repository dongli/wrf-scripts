#! /usr/bin/env python3

import argparse
from glob import glob
import os
import re
import pendulum
import f90nml
from progressbar import ProgressBar, Percentage, Bar
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
import utils import cli, check_files, run, parse_config

def link_update_files(wrfda_root, work_root):
	os.mkdir(work_root)
	os.chdir(work_root)
	run(f'ln -sf {wrfda_root}/var/build/da_update_bc.exe ./')

def run_wrfda_update_lateralbc(work_root, prod_root, wrfda_root, config, args):
	common_config = config['common']

	# Shortcuts
	start_time = common_config['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	
	cli.notice('Prepare work directory.')
	if not os.path.exists(work_root):
		link_update_files(wrfda_root, work_root)
	if args.force:
		run(f'rm -rf {work_root}/*')
		link_update_files(wrfda_root, work_root)
	os.chdir(work_root)
	
	expected_files.expend([f'{prod_root}/wrfbdy_d01', 'wrfinput_d01'])
	if not check_files(expected_files):
		cli.error('da_wrfvar.exe or real.exe wasn\'t executed successfully!')

	for infile in expected_files:
		run(f'cp {infile} ./')

	with open('parame.in', 'w') as f:
		f.writelines("&control_param")
		f.writelines("da_file            = './wrfinput_d01'")
		f.writelines("wrf_bdy_file       = './wrfbdy_d01'")
		f.writelines("update_lateral_bdy = .true. ")
		f.writelines("update_low_bdy     = .false.")
		f.writelines("/")
	if args.verbose:
		run('./da_update_bc.exe')
	else:
		run('./da_update_bc.exe > da_update_bc.out 2>&1')
	run(f'cp ./wrfbdy_d01 {}/wrfbdy_d01'.format(prod_root))
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
    args.work_root = os.path.abspath(args.work_root) + 'UPDATE_LATERALBC'

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

	run_wrfda_update_lateral(args.work_root, args.prod_root, args.wrfda_root, config, args)
