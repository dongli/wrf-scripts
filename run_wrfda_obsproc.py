#! /usr/bin/env python3

import argparse
from glob import glob
from netCDF4 import Dataset 
import os
import re
import pendulum
import f90nml
from progressbar import ProgressBar, Percentage, Bar
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wrfda_obsproc(work_root, prod_root, wrfda_root, littler_root, config, args):
	common_config = config['common']

	# Shortcuts
	start_time = common_config['start_time']
	run_root = work_root + 'OBSPROC'
	if not os.path.exists(run_root):
		os.mkdir(run_root)
		os.chdir(run_root)
		run(f'ln -sf {wrfda_root}/obsproc/obsproc.exe .')
		run(f'ln -sf {wrfda_root}/obsproc/obserr.txt .')
		run( 'ln -sf {}/obs.{} .'.format(littler_root, start_time.format('YYYYMMDDHHmm')
	else:
		if args.force:
			os.rmdir(run_root)
			os.mkdir(run_root)
			os.chdir(run_root)
			run(f'ln -sf {wrfda_root}/obsproc/obsproc.exe .')
			run(f'ln -sf {wrfda_root}/obsproc/obserr.txt .')
			run( 'ln -sf {}/obs.{} .'.format(littler_root, start_time.format('YYYYMMDDHHmm')
		else:
			os.chdir(run_root)

	if check_files([f'{prod_root}/wrfinput_d01']):
		ncfile       = Dataset(f'{prod_root}/wrfinput_d01', 'r')
		iproj        = ncfile.getncattr('MAP_PROJ')
		phic         = ncfile.getncattr('CEN_LAT')
		xlonc        = ncfile.getncattr('CEN_LON')
		moad_cen_lat = ncfile.getncattr('MOAD_CEN_LAT')
		standard_lon = ncfile.getncattr('STAND_LON')
	else:
		iproj        = common_config['map_proj']
		phic         = '{:.5f}'.format(common_config['ref_lat'])
		xlonc        = '{:.1f}'.format(common_config['ref_lon'])
		moad_cen_lat = '{:.5f}'.format(common_config['ref_lat'])
		standard_lon = '{:.1f}'.format(common_config['ref_lon'])

	try:
		if config['wrfda']['ob_format']:
			ob_format = config['wrfda']['ob_format']
	except:
		ob_format = 1

	run(f'cp {os.path.dirname(os.path.realpath(__file__))}/namelists/namelist.obsproc ./')
	namelist_obsproc = f90nml.read('./namelist.obsproc')
	namelist_obsproc['record1']['obs_gts_filename']  = 'obs.{}'.format(start_time.format('YYYYMMDDHHmm'))
	namelist_obsproc['record2']['time_window_min']   =  start_time.subtract(minutes=args.time_window/2).format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record2']['time_analysis']     =  start_time.format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record2']['time_window_max']   =  start_time.add(minutes=args.time_window/2).format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record3']['max_number_of_obs'] = '1200000'
	namelist_obsproc['record7']['PHIC']              =  phic
	namelist_obsproc['record7']['XLONC']             =  xlonc
	namelist_obsproc['record7']['MOAD_CEN_LAT']      =  moad_cen_lat
	namelist_obsproc['record7']['STANDARD_LON']      =  standard_lon
	namelist_obsproc['record8']['NESTIX']            =  common_config['e_sn']
	namelist_obsproc['record8']['NESTJX']            =  common_config['e_we']
	namelist_obsproc['record8']['DIS']               =  common_config['resolution']
	namelist_obsproc['record9']['OUTPUT_OB_FORMAT']  =  ob_format
	namelist_obsproc.write('./namelist.wps', force=True)

	cli.notice('Run obsproc.exe ...')
	expected_files = ['obs_gts_{}.3DVAR'.format(start_time.format('YYYY-MM-DD_HH:mm:ss')]
	if not check_files(expected_files) or args.force:
		run('run -f obs_gts_*')
		if args.verbose:
			run('./obsproc.exe')
		else:
			run('./obsproc.exe > obsproc.out 2>&1')
		if not check_files(expected_files):
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check output {run_root}/obsproc.out')
		cli.notice('Succeeded.')
	else:
		cli.notice('File obs_gts_* already exist.')
	run('ls -l obs_gts_*')
	run(f'cp obs_gts_* {prod_root}')
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS, WRFDA)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-p', '--prod-root', dest='prod_root', help='Produce root directory')
	parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WPS)')	
	parser.add_argument('-l', '--littler-root', dest='littler_root', help='Little_r data root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-t', '--time-window', dest='time_window', help='Time window of data assimilation (min)', default=360, type=int)
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or environment variable WORK_ROOT need to be set!')

	if not args.prod_root:
		if os.getenv('PROD_ROOT'):
			args.work_root = os.getenv('PROD_ROOT')
		else:
			cli.error('Option --prod-root or environment variable PROD_ROOT need to be set!')

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wefda_root = args.codes + '/WRFDA'
		else:
			cli.error('Option --wrfda-root or environment variable WRFDA_ROOT need to be set!')
	
	if not args.littler_root:
		if os.getenv('LITTLER_ROOT'):
			args.littler_root = os.getenv('LITTLER_ROOT')
		else:
			cli.error('Option --littler-root or environment variable LITTLER_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	args.prod_root = os.path.abspath(args.prod_root)
	args.wrfda_root = os.path.abspath(args.wrfda_root)
	args.littler_root = os.path.abspath(args.littler_root)

	config = parse_config(args.config_json)

	run_wrfda_obsproc(args.work_root, args.prod_root, args.wrfda_root, args.littler_root, config, args)



