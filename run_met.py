#!/usr/bin/env python3

import argparse
import pendulum
from jinja2 import Template
import os
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/utils')
from utils import cli, parse_config, edit_file, check_files, run

def run_met(work_root, met_root, config, args):
	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	max_dom = config['domains']['max_dom']

	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	upp_work_dir = work_root + '/upp'
	if not os.path.isdir(upp_work_dir): cli.error('UPP is not run successfully!')

	met_work_dir = work_root + '/met'
	if not os.path.isdir(met_work_dir): os.makedirs(met_work_dir)
	os.chdir(met_work_dir)

	cli.stage('Prepare observation file.')

	if args.littler_root:
		if 'obs' in config['custom']:
			if 'little_r' in config['custom']['obs']:
				dir_pattern = config['custom']['obs']['little_r']['dir_pattern']
				file_pattern = config['custom']['obs']['little_r']['file_pattern']
				obs_dir = Template(dir_pattern).render(obs_time=start_time)
				obs_file = Template(file_pattern).render(obs_time=start_time)
				if not os.path.isfile(f'{args.littler_root}/{obs_dir}/{obs_file}'):
					cli.error(f'Observation {args.littler_root}/{obs_dir}/{obs_file} does not exist!')
				run(f'{met_root}/bin/ascii2nc -format little_r {args.littler_root}/{obs_dir}/{obs_file} ob.nc')
	elif args.prepbufr_root:
		pass

	if not check_files(('ob.nc')):
		cli.error('Failed to prepare netCDF observation file!')

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument(      '--met-root', dest='met_root', help='MET root directory (e.g. MET)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-l', '--littler-root', dest='littler_root', help='LITTLE_R data root directory')
	parser.add_argument('-p', '--prepbufr-root', dest='prepbufr_root', help='PrepBUFR data root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or environment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		os.makedirs(args.work_root)
		cli.notice(f'Create work directory {args.work_root}.')

	if not args.met_root:
		if os.getenv('MET_ROOT'):
			args.met_root = os.getenv('MET_ROOT')
		elif args.codes:
			args.met_root = args.codes + '/MET'
		else:
			cli.error('Option --met-root or environment variable MET_ROOT need to be set!')
	args.met_root = os.path.abspath(args.met_root)
	if not os.path.isdir(args.met_root):
		cli.error(f'Directory {args.met_root} does not exist!')

	config = parse_config(args.config_json)

	run_met(args.work_root, args.met_root, config, args)
