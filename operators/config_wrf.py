#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
from netCDF4 import Dataset
import re
from shutil import copy
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, parse_config, wrf_version, Version

def config_wrf(work_root, wrf_root, wrfda_root, config, args):
	phys_config = config['physics'] if 'physics' in config else {}

	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	max_dom = config['domains']['max_dom']
	
	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wrf_work_dir = work_root + '/wrf'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	version = wrf_version(wrf_root)

	if os.path.isfile(f'{wrf_work_dir}/wrfinput_d01_{start_time_str}'):
		wrfinput = Dataset(f'{wrf_work_dir}/wrfinput_d01_{start_time_str}')
		num_land_cat = wrfinput.getncattr('NUM_LAND_CAT')
		wrfinput.close()
	else:
		num_land_cat = None

	cli.notice('Edit namelist.input for WRF.')
	copy(f'{wrf_root}/run/namelist.input', 'namelist.input')
	namelist_input = f90nml.read('namelist.input')
	namelist_input['time_control']['run_hours']              = config['custom']['forecast_hours']
	namelist_input['time_control']['start_year']             = [int(start_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['start_month']            = [int(start_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['start_day']              = [int(start_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['start_hour']             = [int(start_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['end_year']               = [int(end_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['end_month']              = [int(end_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['end_day']                = [int(end_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['end_hour']               = [int(end_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['frames_per_outfile']     = [1 for i in range(max_dom)]
	if 'background' in config['custom'] and 'interval_seconds' in config['custom']['background']:
		namelist_input['time_control']['interval_seconds']       = config['custom']['background']['interval_seconds']
	if 'time_control' in config:
		for key, value in config['time_control'].items():
			namelist_input['time_control'][key] = value
	for key, value in config['domains'].items():
		namelist_input['domains'][key] = value
	if 'physics_suite' in namelist_input['physics']: del namelist_input['physics']['physics_suite']
	for key, value in phys_config.items():
		namelist_input['physics'][key] = value
	if num_land_cat != None: namelist_input['physics']['num_land_cat'] = num_land_cat
	if 'dynamics' in config:
		for key, value in config['dynamics'].items():
			namelist_input['dynamics'][key] = value
	if version == Version('3.9.1'):
		namelist_input['dynamics']['gwd_opt'] = 0
	namelist_input.write('./namelist.input', force=True)
	
	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
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

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wrfda_root = args.codes + '/WRFDA'
		else:
			cli.error('Option --wrf-root or environment variable WRFDA_ROOT need to be set!')
	args.wrfda_root = os.path.abspath(args.wrfda_root)
	if not os.path.isdir(args.wrfda_root):
		cli.error(f'Directory {args.wrfda_root} does not exist!')

	config = parse_config(args.config_json)

	config_wrf(args.work_root, args.wrf_root, args.wrfda_root, config, args)
