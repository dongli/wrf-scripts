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
from utils import cli, parse_config

def config_wrf(work_root, wrf_root, wps_root, geog_root, config, args):
	pprint(config)
	common_config = config['common']

	start_time = common_config['start_time']
	end_time = common_config['end_time']
	max_dom = common_config['max_dom']
	
	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wps_work_dir = work_root + '/WPS'
	if not os.path.isdir(wps_work_dir): os.mkdir(wps_work_dir)
	os.chdir(wps_work_dir)

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
	namelist_wps['geogrid']['dx']                   = common_config['resolution']
	namelist_wps['geogrid']['dy']                   = common_config['resolution']
	namelist_wps['geogrid']['ref_lat']              = common_config['ref_lat']
	namelist_wps['geogrid']['ref_lon']              = common_config['ref_lon']
	namelist_wps['geogrid']['truelat1']             = common_config['truelat1']
	namelist_wps['geogrid']['truelat2']             = common_config['truelat2']
	namelist_wps['geogrid']['stand_lon']            = common_config['stand_lon']
	namelist_wps['geogrid']['geog_data_path']       = geog_root
	namelist_wps['geogrid']['opt_geogrid_tbl_path'] = wps_work_dir
	namelist_wps['metgrid']['opt_metgrid_tbl_path'] = wps_work_dir
	namelist_wps.write('./namelist.wps', force=True)

	wrf_work_dir = work_root + '/WRF'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	cli.notice('Edit namelist.input for WRF.')
	copy(f'{wrf_root}/run/namelist.input', 'namelist.input')
	namelist_input = f90nml.read('namelist.input')
	namelist_input['time_control']['run_hours']              = common_config['forecast_hours']
	namelist_input['time_control']['start_year']             = [int(start_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['start_month']            = [int(start_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['start_day']              = [int(start_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['start_hour']             = [int(start_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['end_year']               = [int(end_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['end_month']              = [int(end_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['end_day']                = [int(end_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['end_hour']               = [int(end_time.format("H")) for i in range(max_dom)]
	namelist_input['domains']     ['time_step']              = int(common_config['time_step'])
	namelist_input['domains']     ['max_dom']                = max_dom
	namelist_input['domains']     ['e_we']                   = common_config['e_we']
	namelist_input['domains']     ['e_sn']                   = common_config['e_sn']
	namelist_input['domains']     ['dx']                     = [common_config['resolution'] / common_config['parent_grid_ratio'][i] for i in range(max_dom)]
	namelist_input['domains']     ['dy']                     = [common_config['resolution'] / common_config['parent_grid_ratio'][i] for i in range(max_dom)]
	namelist_input['domains']     ['grid_id']                = [i + 1 for i in range(max_dom)]
	namelist_input['domains']     ['parent_id']              = common_config['parent_id']
	namelist_input['domains']     ['i_parent_start']         = common_config['i_parent_start']
	namelist_input['domains']     ['j_parent_start']         = common_config['j_parent_start']
	namelist_input['domains']     ['parent_grid_ratio']      = common_config['parent_grid_ratio']
	namelist_input['domains']     ['parent_time_step_ratio'] = common_config['parent_grid_ratio']
	namelist_input.write('./namelist.input', force=True)
	
	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
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

	if not args.wrf_root:
		if os.getenv('WRF_ROOT'):
			args.wrf_root = os.getenv('WRF_ROOT')
		elif args.codes:
			args.wrf_root = args.codes + '/WRF'
		else:
			cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')
	args.wrf_root = os.path.abspath(args.wrf_root)
	if not os.path.isdir(args.wrf_root):
		cli.error(f'Directory {args.wrf_root} does not exist!')

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

	config_wrf(args.work_root, args.wrf_root, args.wps_root, args.geog_root, config, args)
