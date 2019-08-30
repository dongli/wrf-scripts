#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
from jinja2 import Template
import re
from shutil import copy
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/utils')
from utils import cli, check_files, edit_file, run, parse_config, submit_job

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
		submit_job(f'{wps_root}/geogrid/src/geogrid.exe', args.np, config, args, logfile='geogrid.log.0000', wait=True)
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {os.path.abspath(wps_work_dir)}/geogrid.out.0000')
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
	parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs.', action='store_true')
	parser.add_argument(      '--pbs', help='Use PBS job management system variants (e.g. TORQUE) to run MPI jobs.', action='store_true')
	parser.add_argument(      '--ntasks-per-node', dest='ntasks_per_node', help='Override the default setting.', default=None, type=int)
	parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
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
