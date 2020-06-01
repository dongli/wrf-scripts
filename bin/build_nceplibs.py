#!/usr/bin/env python3

import argparse
import re
import os
import pexpect
import subprocess
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import edit_file, run, cli, check_files

def build_nceplibs(nceplibs_root, args):
	if not 'HDF5' in os.environ:
		res = subprocess.run(['which', 'h5dump'], stdout=subprocess.PIPE)
		if res.returncode == 0:
			os.environ['HDF5'] = os.path.dirname(os.path.dirname(res.stdout.decode('utf-8')))
			cli.notice(f'Set HDF5 to {os.environ["HDF5"]}')
	if not 'HDF5' in os.environ:
		cli.warning('HDF5 environment variable is not set')

	if not 'NETCDF' in os.environ:
		res = subprocess.run(['which', 'ncdump'], stdout=subprocess.PIPE)
		if res.returncode == 0:
			os.environ['NETCDF'] = os.path.dirname(os.path.dirname(res.stdout.decode('utf-8')))
			cli.notice(f'Set NETCDF to {os.environ["NETCDF"]}')
	if not 'NETCDF' in os.environ:
		cli.warning('NETCDF environment variable is not set!')

	if not 'JASPER_INC' in os.environ or not 'JASPER_LIB' in os.environ:
		if 'JASPER_ROOT' in os.environ:
			os.environ['JASPER_INC'] = os.environ['JASPER_ROOT'] + '/include'
			os.environ['JASPER_LIB'] = os.environ['JASPER_ROOT'] + '/lib'
			cli.notice(f'Set JASPER_INC to {os.environ["JASPER_INC"]}.')
			cli.notice(f'Set JASPER_LIB to {os.environ["JASPER_LIB"]}.')
		else:
			cli.error('JASPERINC and JASPERLIB environment variables are not set!')

	if not 'PNG_INC' in os.environ or not 'PNG_LIB' in os.environ:
		if 'LIBPNG_ROOT' in os.environ:
			os.environ['PNG_INC'] = os.environ['LIBPNG_ROOT'] + '/include'
			os.environ['PNG_LIB'] = os.environ['LIBPNG_ROOT'] + '/lib'
		else:
			os.environ['PNG_INC'] = '/usr/include'
			os.environ['PNG_LIB'] = '/usr/lib64'
		cli.notice(f'Set PNG_INC to {os.environ["PNG_INC"]}.')
		cli.notice(f'Set PNG_LIB to {os.environ["PNG_LIB"]}.')

	os.chdir(nceplibs_root)

	if args.compiler_suite == 'gnu':
		# Fix for gfortran 9.1.0.
		edit_file('src/g2/v3.1.0/src/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_8)/=0']], return_on_first_match=True)
		edit_file('src/g2/v3.1.0/src/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_4)/=0']], return_on_first_match=True)
		edit_file('src/g2/v3.1.0/src/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_2)/=0']], return_on_first_match=True)
		edit_file('src/g2/v3.1.0/src/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_1)/=0']], return_on_first_match=True)

	edit_file('make_ncep_libs.sh', [['read -p "Proceed\? \(y/n\) " yn', 'yn=y']])

	run(f'./make_ncep_libs.sh -s linux -c {args.compiler_suite} -d {args.nceplibs_root} -o 0 -a upp')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, UPP)')
	parser.add_argument('-n', '--nceplibs-root', dest='nceplibs_root', help='NCEPlibs root directory (e.g. NCEPLIBS')
	parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'])
	parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
	args = parser.parse_args()

	if not args.nceplibs_root:
		if os.getenv('NCEPLIBS_ROOT'):
			args.nceplibs_root = os.getenv('NCEPLIBS_ROOT')
		elif args.codes:
			args.nceplibs_root = args.codes + '/NCEPLIBS'
		else:
			cli.error('Option --nceplibs-root or environment variable NCEPLIBS_ROOT need to be set!')
	args.nceplibs_root = os.path.abspath(args.nceplibs_root)
	if not os.path.isdir(args.nceplibs_root):
		cli.error(f'Directory {args.nceplibs_root} does not exist!')

	build_nceplibs(args.nceplibs_root, args)
