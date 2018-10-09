#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
import re
from shutil import copyfile
import sys
sys.path.append('./utils')
from utils import cli, check_files, run, parse_config

parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRFDA).')
parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRF for V4)')
parser.add_argument('-w', '--work-dir', dest='work_dir', help='Work directory to run WRFDA.')
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.', required=True)
parser.add_argument('-f', '--force', help='Force to run', action='store_true')
args = parser.parse_args()

if not args.wrfda_root:
	if os.getenv('WRFDA_ROOT'):
		args.wrfda_root = os.getenv('WRFda_ROOT')
	elif args.codes:
		args.wrfda_root = args.codes + '/WRFDA/var'
	else:
		cli.error('Option --wrfda-root or environment variable WRFDA_ROOT need to be set!')

if not args.work_dir:
	args.work_dir = args.wrfda_root + '/run'

config = parse_config(args.config_json)
da_config = config['da']

os.chdir(args.work_dir)

if da_config['cv_options'] == 'cv3':
	cli.notice('Use cv3 option.')
	run(f'cp -p {args.wrfda_root}/run/be.dat.cv3 {args.work_dir}/be.dat')
	cli.notice('Edit namelist.input.')
	namelist_input = f90nml.read(f'{args.wrfda_root}/test/tutorial/namelist.input')
	namelist_input['wrfvar7']['cv_options'] = 3
	namelist_input['wrfvar7']['as1'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as2'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as3'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as4'] = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as5'] = [0.25, 1.0, 1.5]
	namelist_input.write('namelist.input', force=True)
