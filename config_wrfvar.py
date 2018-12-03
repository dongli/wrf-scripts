#! /usr/bin/env python3

import argparse
import os
import pendulum
import f90nml
import re
from shutil import copyfile
from pprint import pprint
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/utils')
from utils import cli, parse_config

def config_wrfvar(work_root, config, dom_id):
	pprint(config)
	common_config = config['common']
	datetime_fmt  = 'YYYY-MM-DD_HH:mm:ss.0000'	

	# Shortcuts
	start_time = common_config['start_time']
	end_time   = common_config['end_time']

	if not os.path.exists(work_root):
		os.mkdir(work_root)

	copyfile(f'{script_root}/namelists/namelist.wrfvar', f'{work_root}/namelist.input')
	
	cli.notice('Edit namelist.input for WRFVAR.')
	time_window  = config['wrfda']['time_window'] if 'time_window' in config['wrfda'] else 360
	namelist_wrfvar = f90nml.read(f'{work_root}/namelist.input')
	for key in config['wrfda']['namelist']:
		for sub_key in config['wrfda']['namelist'][key]:
			namelist_wrfvar[key][sub_key] = config['wrfda']['namelist'][key][sub_key]
	namelist_wrfvar['wrfvar18']['analysis_date']   = start_time.format(datetime_fmt)
	namelist_wrfvar['wrfvar21']['time_window_min'] = start_time.subtract(minutes=time_window/2).format(datetime_fmt)
	namelist_wrfvar['wrfvar22']['time_window_max'] = start_time.add(minutes=time_window/2).format(datetime_fmt)
	namelist_wrfvar['time_control']['start_year']  = start_time.year
	namelist_wrfvar['time_control']['start_month'] = start_time.month
	namelist_wrfvar['time_control']['start_day']   = start_time.day
	namelist_wrfvar['time_control']['start_hour']  = start_time.hour
	namelist_wrfvar['time_control']['end_year']    = start_time.year
	namelist_wrfvar['time_control']['end_month']   = start_time.month
	namelist_wrfvar['time_control']['end_day']     = start_time.day
	namelist_wrfvar['time_control']['end_hour']    = start_time.hour
	namelist_wrfvar['domains']['e_we']             = common_config['e_we'][dom_id-1]
	namelist_wrfvar['domains']['e_sn']             = common_config['e_sn'][dom_id-1]
	namelist_wrfvar['domains']['dx']               = common_config['resolution']/common_config['parent_grid_ratio'][dom_id-1]
	namelist_wrfvar['domains']['dy']               = common_config['resolution']/common_config['parent_grid_ratio'][dom_id-1]
	namelist_wrfvar.write(f'{work_root}/namelist.input', force=True)

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-i', '--dom-id', dest='dom_id', help='Domain id', type=int)
	parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('DOM_ID'):
			args.wrfda_root = os.getenv('DOM_ID')
		else:
			cli.error('Option --dom-id or enviroment variable DOM_ID need to be set!')

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or enviroment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')
	args.work_root = os.path.abspath(args.work_root) + '/WRFVAR'

	config = parse_config(args.config_json)

	config_wrfvar(args.work_root, config, args.dom_id)

