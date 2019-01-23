#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import re
import sys
import config_wrfvar
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wrfda(work_root, prod_root, wrfda_root, config, args):
	common_config = config['common']
	if not 'wrfda' in config:
		cli.error('There is no "wrfda" in configuration file!')
	wrfda_config = config['wrfda']
	
	start_time = common_config['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'

	wrfda_work_dir = os.path.abspath(work_root) + '/WRFDA'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	run(f'ln -sf {wrfda_root}/var/build/da_wrfvar.exe .')
	run(f'ln -sf {wrfda_root}/run/LANDUSE.TBL .')

	if 'cv_options' in wrfda_config:
		if wrfda_config['cv_options'] == 5:
			run(f'ln -sf {prod_root}/be.dat.cv5 be.dat')
		elif wrfda_config['cv_options'] == 6:
			run(f'ln -sf {prod_root}/be.dat.cv6 be.dat')
		elif wrfda_config['cv_options'] == 7:
			run(f'ln -sf {prod_root}/be.dat.cv7 be.dat')
	if not os.path.exists('./be.dat'):
		run(f'ln -sf {wrfda_root}/var/run/be.dat.cv3 be.dat')

	expected_files = ['{}/wrfinput_d{:02d}'.format(prod_root, i+1) for i in range(common_config['max_dom'])]
	if not check_files(expected_files):
		cli.error('real.exe or da_update_bc.exe wasn\'t executed successfully!')

	if wrfda_config['type'] == '3dvar':
		run(f'ln -sf obs_gts_{start_time.format(datetime_fmt}.3DVAR ob.ascii')

	if 'da_domain' in wrfda_config:
		if type(wrfda_config['da_domain']) != list:
			da_domain = [wrfda_config['da_domain']]
	else:
		da_domain = [i+1 for i in range(common_config['max_dom'])]
	for i in da_domain:
		config_wrfvar(work_root, i)
		run(f'{}/wrfinput_d{:02d} ./fg'.format(prod_root, i))
		if args.verbose:
			run(f'mpiexec -np {args.np} ./da_wrfvar.exe')
		else:
			run(f'mpiexec -np {args.np} ./da_wrfvar.exe > da_wrfvar.out 2>&1')
		if not check_files(['wrfvar_output']):
			if args.verbose:
				cli.error('Failed.')
			else:
				cli.error(f'Failed! Check out {work_root}/da_wrfvar.out')
		run('mv ./wrfvar_output {}/wrfinput_{:02d}'.format(prod_root, i))
	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS, WRFDA)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-p', '--prod-root', dest='prod_root', help='Product root directory')
	parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WPS)')    
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
	args.work_root = os.path.abspath(args.work_root)

	if not args.prod_root:
		if os.getenv('PROD_ROOT'):
			args.work_root = os.getenv('PROD_ROOT')
		else:
			cli.error('Option --prod-root or environment variable PROD_ROOT need to be set!')
	args.prod_root = os.path.abspath(args.prod_root)
	if not os.path.isdir(args.prod_root):
		cli.error(f'Directory {args.prod_root} does not exist!')

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

	config = parse_config(args.config_json)

	run_wrfda_obsproc(args.work_root, args.prod_root, args.wrfda_root, config, args)
