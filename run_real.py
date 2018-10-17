#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
from netCDF4 import Dataset
import re
from shutil import copyfile
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_real(wrf_root, wps_root, config, args):
	common_config = config['common']
	
	time_format_str = 'YYYY-MM-DD_HH:mm:ss'
	
	os.chdir(wrf_root + '/run')
	
	cli.notice('Run real.exe ...')
	expected_files = ['wrfinput_d{:02d}'.format(i + 1) for i in range(common_config['max_dom'])]
	expected_files.append('wrfbdy_d01')
	if not check_files(expected_files) or args.force:
		run('rm -f wrfinput_* met_em.*.nc')
		run(f'ln -s {wps_root}/met_em.*.nc .')
		try:
			dataset = Dataset(glob('met_em.*.nc')[0])
		except:
			cli.error('Failed to open one of met_em.*.nc file!')
		namelist_input = f90nml.read('./namelist.input')
		namelist_input['domains']['num_metgrid_levels'] = dataset.dimensions['num_metgrid_levels'].size
		namelist_input['domains']['num_metgrid_soil_levels'] = dataset.dimensions['num_st_layers'].size
		namelist_input.write('./namelist.input', force=True)
		run('./real.exe')
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {os.path.abspath(wrf_root)}/run/rsl.error.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File wrfinput_* already exist.')
	run(f'ls -l {wrf_root}/run/wrfinput_* {wrf_root}/run/wrfbdy_*')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
	parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	args = parser.parse_args()
	
	if not args.wrf_root:
		if os.getenv('WRF_ROOT'):
			args.wrf_root = os.getenv('WRF_ROOT')
		elif args.codes:
			args.wrf_root = args.codes + '/WRF'
		else:
			cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')
	
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

	run_real(args.wrf_root, args.wps_root, config, args)

