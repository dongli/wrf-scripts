#!/usr/bin/env python3.6

import argparse
from glob import glob
import netCDF4
import os
import pendulum
import re
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

time_format_str = 'YYYY-MM-DD_HH:mm:ss'

os.chdir(args.wps_root)

start_date_str = ''
end_date_str = ''
for i in range(config['max_dom']):
	start_date_str += f"'{config['start_time'].format(time_format_str)}', "
	if i == 0:
		end_date_str += f"'{config['end_time'].format(time_format_str)}', "
	else:
		end_date_str += f"'{config['start_time'].format(time_format_str)}', "
cli.notice('Edit namelist.wps.')
edit_file('./namelist.wps', [
	['^\s*max_dom.*$', f' max_dom = {config["max_dom"]},'],
	['^\s*start_date.*$', f' start_date = {start_date_str}'],
	['^\s*end_date.*$', f' end_date = {end_date_str}'],
	['^\s*dx.*$', f' dx = {config["resolution"]},'],
	['^\s*dy.*$', f' dy = {config["resolution"]},'],
	['^\s*ref_lat.*$', f' ref_lat = {config["ref_lat"]},'],
	['^\s*ref_lon.*$', f' ref_lon = {config["ref_lon"]},'],
	['^\s*truelat1.*$', f' truelat1 = {config["truelat1"]},'],
	['^\s*truelat2.*$', f' truelat2 = {config["truelat2"]},'],
	['^\s*stand_lon.*$', f' stand_lon = {config["stand_lon"]},'],
	['^\s*geog_data_path.*$', f' geog_data_path = \'{args.geog_root}\',']
])

cli.notice('Succeeded.')
