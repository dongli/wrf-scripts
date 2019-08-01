#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
from jinja2 import Template
import re
from shutil import copy
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, edit_file, run, parse_config

def run_wps_geogrid(work_root, wps_root, config, args):
	wps_work_dir = os.path.abspath(work_root) + '/wps'
	if not os.path.isdir(wps_work_dir): os.mkdir(wps_work_dir)
	os.chdir(wps_work_dir)

	cli.notice(f'Run geogrid.exe at {wps_work_dir} ...')
	run(f'ln -sf {wps_root}/geogrid/GEOGRID.TBL.ARW {wps_work_dir}/GEOGRID.TBL')
	# FIXME: Why I change GEOGRID.TBL?
	# edit_file('GEOGRID.TBL', [
	#	['rel_path=default:albedo_modis', 'rel_path=default:albedo_ncep'],
	#	['rel_path=default:maxsnowalb_modis', 'rel_path=default:maxsnowalb']
	#])
	expected_files = ['geo_em.d{:02d}.nc'.format(i + 1) for i in range(config['domains']['max_dom'])]
	if not check_files(expected_files):
		run('rm -f geo_em.d*.nc')
		if args.verbose:
			run(f'{wps_root}/geogrid/src/geogrid.exe')
		else:
			run(f'{wps_root}/geogrid/src/geogrid.exe &> geogrid.out')
		if not check_files(expected_files):
			if args.verbose:
				cli.error(f'Failed!')
			else:
				cli.error(f'Failed! Check output {os.path.abspath(wps_work_dir)}/geogrid.out.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File geo_em.*.nc already exist.')
	run(f'ls -l {wps_work_dir}/geo_em.*.nc')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WPS system.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
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

	run_wps_geogrid(args.work_root, args.wps_root, config, args)
