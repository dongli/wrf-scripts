#! /usr/bin/env python3

import argparse
from glob import glob
import os
import re
import pendulum
import f90nml
from progressbar import ProgressBar, Percentage, Bar
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wrfda_obsproc(wrfda_root, littler_root, prod_root, config, args):
	common_config = config['common']

	# Shortcuts
	start_time = common_config['start_time']

	# ??? create a obsproc work dir ???
	# ??? change to obsproc work dir ???

	run(f'ln -sf {wrfda_root}/obsproc/obsproc.exe .')
	run(f'ln -sf {wrfda_root}/obsproc/obserr.txt .')
	run( 'ln -sf {}/obs.{} .'.format(littler_root, start_time.format('YYYYMMDDHHmm')

	wrfout_file  = '{}/wrfout_d01_{}'.format('YYYY-MM-DD_HH:mm:ss')
	iproj        = os.popen(f'ncdump -h {wrfout_file} | grep ":MAP_PROJ =" | awk "{print $3}"')
	phic         = os.popen(f'ncdump -h {wrfout_file} | grep ":CEN_LAT ="  | awk "{print $3}" | sed -e "s/f//g"')
	xlonc        = os.popen(f'ncdump -h {wrfout_file} | grep ":CEN_LON ="  | awk "{print $3}" | sed -e "s/f//g"')
	moad_cen_lat = os.popen(f'ncdump -h {wrfout_file} | grep ":MOAD_CEN_LAT =" | awk "{print $3}" | sed -e "s/f//g"')
	standard_lon = os.popen(f'ncdump -h {wrfout_file} | grep ":STAND_LON =" | awk "{print $3}" | sed -e "s/f//g"')

	# ??? cp namelist ???
	# ??? time_window ???
	namelist_obsproc = f90nml.read('./namelist.obsproc')
	namelist_obsproc['record1']['obs_gts_filename']  = 'obs.{}'.format(start_time.format('YYYYMMDDHHmm'))
	namelist_obsproc['record2']['time_window_min']   =  start_time.subtract(minutes=time_window/2).format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record2']['time_analysis']     =  start_time.format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record2']['time_window_max']   =  start_time.add(minutes=time_window/2).format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record3']['max_number_of_obs'] = '1200000'
	namelist_obsproc['record7']['PHIC']              =  phic
	namelist_obsproc['record7']['XLONC']             =  xlonc
	namelist_obsproc['record7']['MOAD_CEN_LAT']      =  moad_cen_lat
	namelist_obsproc['record7']['STANDARD_LON']      =  standard_lon
	namelist_obsproc['record8']['NESTIX']            =  common_config['e_sn']
	namelist_obsproc['record8']['NESTJX']            =  common_config['e_we']
	namelist_obsproc['record8']['DIS']               =  common_config['resolution']
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
				cli.error('Failed! Check output {} ????') # ???
		cli.notice('Succeeded.')
	else:
		cli.notice('File obs_gts_* already exist.')
	run('ls -l obs_gts_*')
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS, WRFDA)')
	parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WPS)')
	parser.add_argument('-l', '--littler-root', dest='littler_root', help='Little_r data root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wefda_root = args.codes + '/DA'
		else:
			cli.error('Option --wrfda-root or environment variable WRFDA_ROOT need to be set!')

	args.wrfda_root = os.path.abspath(args.wrfda_root)

	config = parse_config(args.config_json)

	run_wrfda_obsproc(args.wrfda_root, args.littler_root, args.prod_root, config, args)



