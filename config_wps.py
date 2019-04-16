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
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, parse_config, wrf_version, Version

def config_wps(work_root, wps_root, geog_root, config, args):
	pprint(config)
	common_config = config['common']

	start_time = common_config['start_time']
	end_time = common_config['end_time']
	max_dom = common_config['max_dom']

	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wps_work_dir = work_root + '/wps'
	if not os.path.isdir(wps_work_dir): os.mkdir(wps_work_dir)
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
	namelist_wps['geogrid']['parent_id']            = common_config['parent_id']
	namelist_wps['geogrid']['parent_grid_ratio']    = common_config['parent_grid_ratio']
	namelist_wps['geogrid']['i_parent_start']       = common_config['i_parent_start']
	namelist_wps['geogrid']['j_parent_start']       = common_config['j_parent_start']
	namelist_wps['geogrid']['e_we']                 = common_config['e_we']
	namelist_wps['geogrid']['e_sn']                 = common_config['e_sn']
	namelist_wps['geogrid']['dx']                   = common_config['dx']
	namelist_wps['geogrid']['dy']                   = common_config['dy']
	namelist_wps['geogrid']['map_proj']             = common_config['map_proj']
	namelist_wps['geogrid']['ref_lat']              = common_config['ref_lat']
	namelist_wps['geogrid']['ref_lon']              = common_config['ref_lon']
	namelist_wps['geogrid']['truelat1']             = common_config['truelat1']
	namelist_wps['geogrid']['truelat2']             = common_config['truelat2']
	namelist_wps['geogrid']['stand_lon']            = common_config['stand_lon']
	namelist_wps['geogrid']['geog_data_path']       = geog_root
	namelist_wps['geogrid']['opt_geogrid_tbl_path'] = wps_work_dir
	namelist_wps['metgrid']['opt_metgrid_tbl_path'] = wps_work_dir
	namelist_wps.write('./namelist.wps', force=True)

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
