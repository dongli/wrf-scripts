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

def run_real(work_root, prod_root, wrf_root, config, args):
	common_config = config['common']

	time_format_str = 'YYYY-MM-DD_HH:mm:ss'

	wps_work_dir = os.path.abspath(work_root) + '/WPS'
	if not os.path.isdir(wps_work_dir): os.mkdir(wps_work_dir)
	wrf_work_dir = os.path.abspath(work_root) + '/WRF'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	# ------------------------------------------------------------------------------------------------
	#                                           REAL
	cli.notice('Run real.exe ...')
	expected_files = ['wrfinput_d{:02d}'.format(i + 1) for i in range(common_config['max_dom'])]
	expected_files.append('wrfbdy_d01')
	if not check_files(expected_files) or args.force:
		run('rm -f wrfinput_* met_em.*.nc')
		run(f'ln -s {wps_work_dir}/met_em.*.nc .')
		try:
			dataset = Dataset(glob('met_em.*.nc')[0])
		except:
			cli.error('Failed to open one of met_em.*.nc file!')
		namelist_input = f90nml.read('./namelist.input')
		namelist_input['domains']['num_metgrid_levels'] = dataset.dimensions['num_metgrid_levels'].size
		if 'num_st_layers' in dataset.dimensions:
			namelist_input['domains']['num_metgrid_soil_levels'] = dataset.dimensions['num_st_layers'].size
		else:
			cli.warning(f'Dimension num_st_layers is not in {dataset.filepath()}! Set num_metgrid_soil_levels to 0.')
			namelist_input['domains']['num_metgrid_soil_levels'] = 0
		namelist_input.write('./namelist.input', force=True)
		run(f'{wrf_root}/run/real.exe')
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {os.path.abspath(wrf_work_dir)}/rsl.error.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File wrfinput_* already exist.')
	run(f'ls -l {wrf_work_dir}/wrfinput_* {wrf_work_dir}/wrfbdy_*')
	run(f'cp wrfinput_* wrfbdy_* {prod_root}')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-p', '--prod-root', dest='prod_root', help='Product root directory')
	parser.add_argument('-r', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
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

	if not args.prod_root:
		if os.getenv('PROD_ROOT'):
			args.work_root = os.getenv('PROD_ROOT')
		else:
			cli.error('Option --prod-root or environment variable PROD_ROOT need to be set!')
	args.prod_root = os.path.abspath(args.prod_root)
	if not os.path.isdir(args.prod_root):
		cli.error(f'Directory {args.prod_root} does not exist!')

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

	config = parse_config(args.config_json)

	run_real(args.work_root, args.prod_root, args.wrf_root, config, args)

