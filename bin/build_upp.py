#!/usr/bin/env python3

import argparse
import re
import os
import pexpect
import subprocess
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import edit_file, run, cli, check_files, upp_version, Version

def build_upp(wrf_root, upp_root, args):
	if wrf_root != None: os.environ['WRF_DIR'] = wrf_root

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

	if not 'JASPERINC' in os.environ or not 'JASPERLIB' in os.environ:
		if 'JASPER_ROOT' in os.environ:
			os.environ['JASPERINC'] = os.environ['JASPER_ROOT'] + '/include'
			os.environ['JASPERLIB'] = os.environ['JASPER_ROOT'] + '/lib'
			cli.notice(f'Set JASPERINC to {os.environ["JASPERINC"]}.')
			cli.notice(f'Set JASPERLIB to {os.environ["JASPERLIB"]}.')
		else:
			cli.error('JASPERINC and JASPERLIB environment variables are not set!')

	version = upp_version(args.upp_root)

	if version < Version('4.1'):
		expected_exe_files = ('bin/copygb.exe', 'bin/ndate.exe', 'bin/unipost.exe')
	else:
		expected_exe_files = ('exec/unipost.exe')
		if not check_files(expected_exe_files):
			if not args.nceplibs_root:
				args.nceplibs_root = f'{os.path.dirname(args.upp_root)}/NCEPLIBS'
			if not os.path.isdir(args.nceplibs_root):
				cli.error('NCEPLIBS is not ready!')
		os.environ['NCEPLIBS_DIR'] = args.nceplibs_root

	if not check_files(expected_exe_files):
		os.chdir(upp_root)
		if args.force: run('./clean -a &> /dev/null')
		cli.notice('Configure UPP ...')
		child = pexpect.spawn('./configure')
		child.expect('Enter selection.*')
		if args.compiler_suite == 'intel':
			child.sendline('4')  # Linux x86_64, Intel compiler (dmpar)
		elif args.compiler_suite == 'gnu':
			child.sendline('8')  # Linux x86_64, gfortran compiler (dmpar)
		elif args.compiler_suite == 'pgi':
			child.sendline('14') # Linux x86_64, PGI compiler: -f90=pgf90  (dmpar)
		child.wait()

		if args.compiler_suite == 'intel':
			edit_file('./configure.upp', [
				['mpif90', 'mpiifort'],
				['mpicc', 'mpiicc']
			])

		if 'LIBPNG_ROOT' in os.environ:
			edit_file('./configure.upp', [
				['-lpng', f'-L{os.environ["LIBPNG_ROOT"]}/lib -lpng'],
				['GRIB2SUPT_INC\s*=\s*(.*)', f'GRIB2SUPT_INC = \\1 -I{os.environ["LIBPNG_ROOT"]}/include']
			])

		cli.notice('Compile UPP ...')
		run('./compile &> compile.out')
	
		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			cli.error(f'Failed! Check {upp_root}/compile.out')
	else:
		cli.notice('UPP is already built.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, UPP)')
	parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
	parser.add_argument('-u', '--upp-root', dest='upp_root', help='UPP root directory (e.g. UPP)')
	parser.add_argument('-n', '--nceplibs-root', dest='nceplibs_root', help='NCEPLIBS root directory (e.g. NCEPLIBS')
	parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'])
	parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
	args = parser.parse_args()

	if not args.upp_root:
		if os.getenv('UPP_ROOT'):
			args.upp_root = os.getenv('UPP_ROOT')
		elif args.codes:
			args.upp_root = args.codes + '/UPP'
		else:
			cli.error('Option --upp-root or environment variable UPP_ROOT need to be set!')
	args.upp_root = os.path.abspath(args.upp_root)
	if not os.path.isdir(args.upp_root):
		cli.error(f'Directory {args.upp_root} does not exist!')

	version = upp_version(args.upp_root)

	if version < Version('4.0'):
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

	build_upp(args.wrf_root, args.upp_root, args)
