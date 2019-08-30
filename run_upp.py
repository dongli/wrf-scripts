#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
import re
from math import radians, cos, sin, asin, sqrt
from shutil import copy
from pprint import pprint
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/utils')
from utils import cli, parse_config, edit_file, run

def run_upp(work_root, upp_root, config, args):
	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	max_dom = config['domains']['max_dom']

	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wrf_work_dir = work_root + '/wrf'
	if not os.path.isdir(wrf_work_dir): cli.error('WRF is not run successfully!')

	upp_work_dir = work_root + '/upp'
	if not os.path.isdir(upp_work_dir): os.makedirs(upp_work_dir)
	os.chdir(upp_work_dir)

	if not os.path.isdir(f'{upp_work_dir}/parm'): run(f'mkdir {upp_work_dir}/parm')
	if not os.path.isdir(f'{upp_work_dir}/postprd'): run(f'mkdir {upp_work_dir}/postprd')

	run(f'cp {upp_root}/parm/postxconfig-NT-WRF.txt {upp_work_dir}/parm')
	run(f'cp {upp_root}/scripts/run_unipost {upp_work_dir}/postprd')

	edit_file('./postprd/run_unipost', [
		['/bin/ksh', '/bin/bash'],
		['TOP_DIR=.*', f'TOP_DIR={upp_root}'],
		['DOMAINPATH=.*', f'DOMAINPATH={upp_work_dir}'],
		['UNIPOST_HOME=.*', f'UNIPOST_HOME={upp_root}'],
		['modelDataPath=.*', f'modelDataPath={wrf_work_dir}'],
		['startdate=.*', f'startdate={start_time.format("YYYYMMDDHH")}'],
		['lastfhr=.*', f'lastfhr={(end_time - start_time).hours}'],
		['incrementhr=.*', f'incrementhr=01'],
		['domain_list=.*', f'domain_list="d02"']
	])

	run(f'./postprd/run_unipost')

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--upp-root', dest='upp_root', help='UPP root directory (e.g. UPP)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
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

	if not args.upp_root:
		if os.getenv('UPP_ROOT'):
			args.upp_root = os.getenv('UPP_ROOT')
		elif args.codes:
			args.upp_root = args.codes + '/UPP'
		else:
			cli.error('Option --upp-root or environment variable UPP_ROOT need to be set!')
	args.upp_root = os.path.abspath(args.upp_root)
	if not os.path.isdir(args.upp_root):
		cli.error(f'Directory {args.upp_root} does not exist!')

	config = parse_config(args.config_json)

	run_upp(args.work_root, args.upp_root, config, args)
