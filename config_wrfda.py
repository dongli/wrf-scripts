#! /usr/bin/env python3

import argparse
import os
import pendulum
import f90nml
import re
from io import StringIO
from shutil import copyfile
from pprint import pprint
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/utils')
from utils import cli, parse_config

def config_wrfda(work_root, wrfda_root, config, args):
	common_config = config['common']
	if not 'wrfda' in config:
		cli.error('There is no "wrfda" in configuration file!')
	wrfda_config = config['wrfda']

	start_time = common_config['start_time']
	datetime_fmt  = 'YYYY-MM-DD_HH:mm:ss.0000'	

	wrfda_work_dir = os.path.abspath(work_root) + '/WRFDA'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	time_window  = config['wrfda']['time_window'] if 'time_window' in config['wrfda'] else 360
	# Read in namelist template (not exact Fortran namelist format, we need to change it).
	template = open(f'{wrfda_root}/var/README.namelist').read()
	template = re.sub(r'^[^&]*', '', template, flags=re.DOTALL)
	template = re.sub(r';.*', '', template)
	template = re.sub(r'\([^\)]*\)', '', template)
	namelist_input = f90nml.read(StringIO(template))
	namelist_input['wrfvar1']['var4d_lbc'] = False
	namelist_input['wrfvar6']['orthonorm_gradient'] = True
	namelist_input['wrfvar18']['analysis_date'] = start_time.format(datetime_fmt)
	namelist_input['wrfvar21']['time_window_min'] = start_time.subtract(minutes=time_window/2).format(datetime_fmt)
	namelist_input['wrfvar22']['time_window_max'] = start_time.add(minutes=time_window/2).format(datetime_fmt)
	# Fix bugs
	namelist_input['wrfvar2']['qc_rej_both'] = False
	namelist_input['wrfvar7']['cv_options'] = wrfda_config['cv_options']
	namelist_input['wrfvar14']['rtminit_satid'] = -1
	namelist_input['wrfvar14']['rtminit_sensor'] = -1
	# Merge namelist.input in tutorial.
	tmp = f90nml.read(f'{wrfda_root}/var/test/tutorial/namelist.input')
	for key, value in tmp.items():
		if not key in namelist_input:
			namelist_input[key] = value
	namelist_input['domains']['e_we'] = common_config['e_we']
	namelist_input['domains']['e_sn'] = common_config['e_sn']
	# TODO: Set vertical levels somewhere?
	namelist_input['domains']['e_vert'] = 33
	namelist_input['domains']['dx'] = common_config['resolution']
	namelist_input['domains']['dy'] = common_config['resolution']
	namelist_input.write(f'{wrfda_work_dir}/namelist.input', force=True)

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')	
	parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wrfda_root = args.codes + '/WRFDA'
		else:
			cli.error('Option --wrfda-root or environment variable WRFDA_ROOT need to be set!')
	args.wrfda_root = os.path.abspath(args.wrfda_root)
	if not os.path.isdir(args.wrfda_root):
		cli.error(f'Directory {args.wrfda_root} does not exist!')

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or enviroment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

	config = parse_config(args.config_json)

	config_wrfda(args.wrfda_root, args.work_root, config, args)
