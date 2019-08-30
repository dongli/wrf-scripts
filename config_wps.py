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
from utils import cli, parse_config, wrf_version, Version, run

def config_wps(work_root, wps_root, geog_root, config, args):
	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	max_dom = config['domains']['max_dom']

	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wps_work_dir = work_root + '/wps'
	if not os.path.isdir(wps_work_dir): os.makedirs(wps_work_dir)
	os.chdir(wps_work_dir)

	version = wrf_version(wps_root)
	if version < Version('3.9.1'):
		cli.error(f'WPS {version} may not handle GFS data correctly! Please use WPS >= 3.9.1.')

	cli.notice('Edit namelist.wps for WPS.')
	copy(f'{wps_root}/namelist.wps', 'namelist.wps')
	namelist_wps = f90nml.read('namelist.wps')
	namelist_wps['share']  ['max_dom']              = max_dom
	namelist_wps['share']  ['start_date']           = [start_time_str for i in range(max_dom)]
	namelist_wps['share']  ['end_date']             = [end_time_str if i == 0 else start_time_str for i in range(max_dom)]
	if 'background' in config['custom'] and 'interval_seconds' in config['custom']['background']:
		namelist_wps['share']  ['interval_seconds']   = config['custom']['background']['interval_seconds']
	namelist_wps['geogrid']['geog_data_path']       = geog_root
	for key, value in config['geogrid'].items():
		namelist_wps['geogrid'][key] = value
	namelist_wps['geogrid']['opt_geogrid_tbl_path'] = wps_work_dir
	namelist_wps['metgrid']['opt_metgrid_tbl_path'] = wps_work_dir
	namelist_wps.write('./namelist.wps', force=True)
	run(f'ncl {script_root}/plots/plot_domains.ncl > /dev/null')
	cli.notice(f'Check {wps_work_dir}/wps_show_dom.pdf for domains.')

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-g', '--geog-root', dest='geog_root', help='GEOG data root directory (e.g. WPS_GEOG)')
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

	if not args.geog_root:
		if os.getenv('WPS_GEOG_ROOT'):
			args.geog_root = os.getenv('WPS_GEOG_ROOT')
		elif args.codes:
			args.geog_root = args.codes + '/WPS_GEOG'
		else:
			cli.error('Option --geog-root or environment variable WPS_GEOG_ROOT need to be set!')
	args.geog_root = os.path.abspath(args.geog_root)
	if not os.path.isdir(args.geog_root):
		cli.error(f'Directory {args.geog_root} does not exist!')

	config = parse_config(args.config_json)

	config_wps(args.work_root, args.wps_root, args.geog_root, config, args)
