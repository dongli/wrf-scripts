#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
import json
import re
from shutil import copyfile
import sys
sys.path.append('./utils')
from utils import cli, edit_file, check_files, run, parse_config

parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRFDA).')
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
parser.add_argument('--work-dir', dest='work_dir', help='Work directory to run WRFDA.')
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.', required=True)
parser.add_argument('-f', '--force', help='Force to run', action='store_true')
args = parser.parse_args()

if not args.wrf_root:
	if os.getenv('WRF_ROOT'):
		args.wrf_root = os.getenv('WRF_ROOT')
	elif args.codes:
		args.wrf_root = args.codes + '/WRF'
	else:
		cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')

if not args.wrfda_root:
	if os.getenv('WRFDA_ROOT'):
		args.wrfda_root = os.getenv('WRFda_ROOT')
	elif args.codes:
		args.wrfda_root = args.codes + '/WRFDA'
	else:
		cli.error('Option --wrfda-root or environment variable WRFDA_ROOT need to be set!')

if not args.work_dir:
	args.work_dir = args.wrfda_root + '/var/run'
wrf_work_dir   = args.work_dir + '/fc'
wrfda_work_dir = args.work_dir + '/da'

config = parse_config(args.config_json)
da_config = config['da']

if da_config['cv_options'] != 'cv3' and not os.path.isdir(wrf_work_dir):
	cli.notice(f'Create directory {wrf_work_dir}.')
	os.makedirs(wrf_work_dir)
if not os.path.isdir(wrfda_work_dir):
	cli.notice(f'Create directory {wrfda_work_dir}.')
	os.makedirs(wrfda_work_dir)

if da_config['cv_options'] == 'cv3':
	os.chdir(wrfda_work_dir)
	cli.notice('Use cv3 option.')
	run(f'cp -p {args.wrfda_root}/var/run/be.dat.cv3 {wrfda_work_dir}/be.dat')
	cli.notice('Edit namelist.input for WRFDA.')
	namelist_input = f90nml.read(f'{args.wrfda_root}/var/test/tutorial/namelist.input')
	namelist_input['wrfvar7']['cv_options'] = 3
	namelist_input['wrfvar7']['as1'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as2'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as3'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as4'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as5'] = [0.25, 1.0, 1.5]
	namelist_input.write('namelist.input', force=True)
elif da_config['cv_options'] == 'cv5':
	os.chdir(wrfda_work_dir)
	cli.notice('Use cv5 option.')
	cli.notice('Edit namelist.input for WRFDA.')
	namelist_input = f90nml.read(f'{args.wrfda_root}/var/test/tutorial/namelist.input')
	namelist_input['wrfvar7']['cv_options'] = 5
	namelist_input.write('namelist.input', force=True)

	os.chdir(wrf_work_dir)
	cli.notice('Edit namelist.input for WRF.')
	namelist_input = f90nml.read(f'{args.wrf_root}/run/namelist.input')
	namelist_input['time_control']['history_interval'] = da_config['nmc']['short_forecast_hours'] * 60
	namelist_input['time_control']['frames_per_outfile'] = 1
	namelist_input.write('namelist.input', force=True)

	config['common']['start_time'] = da_config['nmc']['start_time']
	config['common']['forecast_hours'] = da_config['nmc']['short_forecast_hours']

	cli.notice(f'Edit {args.wrfda_root}/var/scripts/gen_be/gen_be_wrapper.ksh')
	edit_file(f'{args.wrfda_root}/var/scripts/gen_be/gen_be_wrapper.ksh', [
		['^\s*export WRFVAR_DIR=.*$',    f'export WRFVAR_DIR={args.wrfda_root}'],
		['^\s*export NL_CV_OPTIONS=.*$', f'export NL_CV_OPTIONS=5'],
		['^\s*export START_DATE=.*$',    f'export START_DATE={da_config["nmc"]["start_time"]}'],
		['^\s*export END_DATE=.*$',      f'export END_DATE={da_config["nmc"]["end_time"]}'],
		['^\s*export FC_DIR=.*$',        f'export FC_DIR={wrf_work_dir}'],
		['^\s*export RUN_DIR=.*$',       f'export RUN_DIR={wrfda_work_dir}/gen_be']
	])
elif da_config['cv_options'] == 'cv6':
	pass
elif da_config['cv_options'] == 'cv7':
	pass
