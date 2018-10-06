#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import re
from math import radians, cos, sin, asin, sqrt
from shutil import copyfile
import sys
sys.path.append('./utils')
from utils import cli, edit_file, parse_config

parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument('-g', '--geog-root', dest='geog_root', help='GEOG data root directory (e.g. WPS_GEOG)')
parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
parser.add_argument('-f', '--force', help='Force to run', action='store_true')
args = parser.parse_args()

script_root = os.path.dirname(os.path.realpath(__file__))

if not args.wrf_root:
	if os.getenv('WRF_ROOT'):
		args.wrf_root = os.getenv('WRF_ROOT')
	elif args.codes:
		args.wrf_root = args.codes + '/WRF'
	else:
		cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')

args.wrf_root = os.path.abspath(args.wrf_root)

if not args.wps_root:
	if os.getenv('WPS_ROOT'):
		args.wps_root = os.getenv('WPS_ROOT')
	elif args.codes:
		args.wps_root = args.codes + '/WPS'
	else:
		cli.error('Option --wps-root or environment variable WPS_ROOT need to be set!')

args.wps_root = os.path.abspath(args.wps_root)

if not args.geog_root:
	if os.getenv('WPS_GEOG_ROOT'):
		args.geog_root = os.getenv('WPS_GEOG_ROOT')
	elif args.codes:
		args.geog_root = args.codes + '/WPS_GEOG'
	else:
		cli.error('Option --geog-root or environment variable WPS_GEOG_ROOT need to be set!')

args.geog_root = os.path.abspath(args.geog_root)

config = parse_config(args.config_json)
common_config = config['common']

# Shortcuts
start_time = common_config['start_time']
end_time = common_config['end_time']
max_dom = common_config['max_dom']
ref_lon = common_config['ref_lon']
ref_lat = common_config['ref_lat']
truelat1 = common_config['truelat1']
truelat2 = common_config['truelat2']
stand_lon = common_config['stand_lon']
dx = common_config['resolution']
dy = common_config['resolution']
parent_id = common_config['parent_id']
grid_ratio = common_config['parent_grid_ratio']
i_parent_start = common_config['i_parent_start']
j_parent_start = common_config['j_parent_start']
e_we = common_config['e_we']
e_sn = common_config['e_sn']

time_format_str = 'YYYY-MM-DD_HH:mm:ss'

os.chdir(args.wps_root)

start_date_str = ''
end_date_str = ''
for i in range(common_config['max_dom']):
	start_date_str += f"'{start_time.format(time_format_str)}', "
	if i == 0:
		end_date_str += f"'{end_time.format(time_format_str)}', "
	else:
		end_date_str += f"'{start_time.format(time_format_str)}', "

cli.notice('Edit namelist.wps for WPS.')
edit_file('./namelist.wps', [
	['^\s*max_dom.*$',           f' max_dom    = {max_dom},'],
	['^\s*start_date.*$',        f' start_date = {start_date_str}'],
	['^\s*end_date.*$',          f' end_date   = {end_date_str}'],
	['^\s*dx.*$',                f' dx         = {dx},'],
	['^\s*dy.*$',                f' dy         = {dy},'],
	['^\s*e_we.*$',              f' e_we       = {str.join(", ", [str(e_we[i]) for i in range(max_dom)])},'],
	['^\s*e_sn.*$',              f' e_sn       = {str.join(", ", [str(e_sn[i]) for i in range(max_dom)])},'],
	['^\s*parent_id.*$',         f' parent_id         = {str.join(", ", [str(parent_id[i]) for i in range(max_dom)])},'],
	['^\s*parent_grid_ratio.*$', f' parent_grid_ratio = {str.join(", ", [str(grid_ratio[i]) for i in range(max_dom)])},'],
	['^\s*i_parent_start.*$',    f' i_parent_start    = {str.join(", ", [str(i_parent_start[i]) for i in range(max_dom)])},'],
	['^\s*j_parent_start.*$',    f' j_parent_start    = {str.join(", ", [str(j_parent_start[i]) for i in range(max_dom)])},'],
	['^\s*ref_lat.*$',           f' ref_lat    = {ref_lat},'],
	['^\s*ref_lon.*$',           f' ref_lon    = {ref_lon},'],
	['^\s*truelat1.*$',          f' truelat1   = {truelat1},'],
	['^\s*truelat2.*$',          f' truelat2   = {truelat2},'],
	['^\s*stand_lon.*$',         f' stand_lon  = {stand_lon},'],
	['^\s*geog_data_path.*$',    f" geog_data_path = '{args.geog_root}',"]
])

os.chdir(args.wrf_root + '/run')

cli.notice('Edit namelist.input for WRF.')
edit_file('./namelist.input', [
	['^\s*run_hours.*$',   f' run_hours   = {common_config["forecast_hour"]},'],
	['^\s*start_year.*$',  f' start_year  = {str.join(", ", [str(start_time.format("Y")) for i in range(max_dom)])},'],
	['^\s*start_month.*$', f' start_month = {str.join(", ", [str(start_time.format("M")) for i in range(max_dom)])},'],
	['^\s*start_day.*$',   f' start_day   = {str.join(", ", [str(start_time.format("D")) for i in range(max_dom)])},'],
	['^\s*start_hour.*$',  f' start_hour  = {str.join(", ", [str(start_time.format("H")) for i in range(max_dom)])},'],
	['^\s*end_year.*$',    f' end_year    = {str.join(", ", [str(end_time.format("Y")) for i in range(max_dom)])},'],
	['^\s*end_month.*$',   f' end_month   = {str.join(", ", [str(end_time.format("M")) for i in range(max_dom)])},'],
	['^\s*end_day.*$',     f' end_day     = {str.join(", ", [str(end_time.format("D")) for i in range(max_dom)])},'],
	['^\s*end_hour.*$',    f' end_hour    = {str.join(", ", [str(end_time.format("H")) for i in range(max_dom)])},'],
	['^\s*max_dom.*$',     f' max_dom     = {max_dom},'],
	['^\s*dx.*$',          f' dx          = {str.join(", ", [str(dx / grid_ratio[i]) for i in range(max_dom)])},'],
	['^\s*dy.*$',          f' dy          = {str.join(", ", [str(dy / grid_ratio[i]) for i in range(max_dom)])},'],
	['^\s*e_we.*$',        f' e_we  = {str.join(", ", [str(e_we[i]) for i in range(max_dom)])},'],
	['^\s*e_sn.*$',        f' e_sn  = {str.join(", ", [str(e_sn[i]) for i in range(max_dom)])},'],
	['^\s*parent_grid_ratio.*$', f' parent_grid_ratio = {str.join(", ", [str(grid_ratio[i]) for i in range(max_dom)])},'],
	['^\s*parent_time_step_ratio.*$', f' parent_time_step_ratio = {str.join(", ", [str(grid_ratio[i]) for i in range(max_dom)])},'],
])

cli.notice('Succeeded.')
