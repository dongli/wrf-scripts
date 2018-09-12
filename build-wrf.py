#!/usr/bin/env python3.6

import argparse
import fileinput
import os
import pexpect
import re
from shutil import copyfile

parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRFV3, WPS)')
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument('-v', '--wrf-major', dest='wrf_major', help='WRF major version (e.g. 3, 4)', default='4')
parser.add_argument('-b', '--use-hyb', dest='use_hyb', help='Use hybrid vertical coordinate', action='store_true')
parser.add_argument('-g', '--use-grib', dest='use_grib', help='Use GRIB IO capability of WRF', action='store_true')
parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'])
parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
args = parser.parse_args()

if not args.wrf_root:
	if os.getenv('WRF_ROOT'):
		args.wrf_root = os.getenv('WRF_ROOT')
	elif args.codes:
		if args.wrf_major == '3':
			args.wrf_root = args.codes + '/WRFV3'
		elif args.wrf_major == '4':
			args.wrf_root = args.codes + '/WRF'
	else:
		print('[Error]: Option --wrf-root or environment variable WRF_ROOT need to be set!')
		exit(1)

if not args.wps_root:
	if os.getenv('WPS_ROOT'):
		args.wps_root = os.getenv('WPS_ROOT')
	elif args.codes:
		args.wps_root = args.codes + '/WPS'
	else:
		print('[Error]: Option --wps-root or environment variable WPS_ROOT need to be set!')
		exit(1)

def check_build_result(expected_exe_files):
	result = True
	for exe in expected_exe_files:
		if not os.path.isfile(exe):
			result = False
			break
	return result

def edit_file(filepath, changes):
	try:
		with fileinput.FileInput(filepath, inplace=True) as file:
			for line in file:
				found = False
				for change in changes:
					if re.search(change[0], line, re.I):
						print(line.replace(change[0], change[1]))
						found = True
						break
				if not found:
					print(line, end='')
	except Exception as e:
		print('[Error]: Failed to edit file {}! {}'.format(filepath, e))
		exit(1)

owd = os.getcwd()

os.chdir(args.wrf_root)
if args.force: os.system('./clean -a 1> /dev/null 2>&1')
if not check_build_result(('main/wrf.exe', 'main/real.exe', 'main/ndown.exe', 'main/tc.exe')):
	# Fix bug when find netcdf.
	#edit_file('./configure', [
	#	['if \[ -f "$NETCDF/lib/libnetcdff.a" -o -f "$NETCDF/lib/libnetcdff.so" \] ; then',
	#	 'if \[ -f "$NETCDF/lib64/libnetcdff.a" -o -f "$NETCDF/lib64/libnetcdff.so" -o -f "$NETCDF/lib/libnetcdff.a" -o -f "$NETCDF/lib/libnetcdff.so" \] ; then'],
	#	['if \[ -f "$NETCDF/lib/libnetcdf.a" -o -f "$NETCDF/lib/libnetcdf.so" \] ; then',
	#	 'if \[ -f "$NETCDF/lib64/libnetcdf.a" -o -f "$NETCDF/lib64/libnetcdf.so" -o -f "$NETCDF/lib/libnetcdf.a" -o -f "$NETCDF/lib/libnetcdf.so" \] ; then']
	#])
	print('[Notice]: Configure WRF ...')
	if args.use_grib:
		print('[Notice]: Set GRIB2 flag.')
		edit_file('./arch/Config.pl', [
			['$I_really_want_to_output_grib2_from_WRF = "FALSE"', '$I_really_want_to_output_grib2_from_WRF = "TRUE"']
		])
	if args.wrf_major == '3' and args.use_hyb:
		child = pexpect.spawn('./configure -hyb')
	else:
		child = pexpect.spawn('./configure')
	child.expect('Enter selection.*')
	if args.compiler_suite == 'intel':
		child.sendline('15')
	elif args.compiler_suite == 'gnu':
		child.sendline('34')
	elif args.compiler_suite == 'pgi':
		child.sendline('54')
	child.expect('Compile for nesting.*')
	child.sendline('1')
	child.wait()

	if args.compiler_suite == 'pgi':
		edit_file('./configure.wrf', [
			['pgf90', 'pgfortran'],
			['mpif90', 'mpifort']
		])

	print('[Notice]: Compile WRF ...')
	os.system('./compile em_real > compile.out 2>&1')
	
	if check_build_result(('main/wrf.exe', 'main/real.exe', 'main/ndown.exe', 'main/tc.exe')):
		print('[Notice]: Succeeded.')
	else:
		print('[Error]: Failed! Check {}/compile.out'.format(args.wrf_root))
		os.chdir(owd)
		exit(1)
else:
	print('[Notice]: WRF is already built.')

os.chdir(owd)

os.chdir(args.wps_root)
if args.force: os.system('./clean -a 1> /dev/null 2>&1')
if not check_build_result(('geogrid/src/geogrid.exe', 'metgrid/src/metgrid.exe', 'ungrib/src/ungrib.exe')):
	# Fix bug when find netcdf.
	#edit_file('./configure', [
	#	['if [ -f "$NETCDF/lib/libnetcdff.a" ] ; then',
	#	 'if [ -f "$NETCDF/lib/libnetcdff.a" -o -f "$NETCDF/lib64/libnetcdff.a" -o -f "$NETCDF/lib/libnetcdff.so" -o -f "$NETCDF/lib64/libnetcdff.so" ] ; then']
	#])
	print('[Notice]: Configure WPS ...')
	child = pexpect.spawn('./configure')
	child.expect('Enter selection.*')
	if args.compiler_suite == 'intel':
		child.sendline('19')
	elif args.compiler_suite == 'gnu':
		child.sendline('3')
	elif args.compiler_suite == 'pgi':
		child.sendline('7')
	child.wait()

	if args.compiler_suite == 'pgi':
		edit_file('./configure.wrf', [
			['pgf90', 'pgfortran'],
			['mpif90', 'mpifort']
		])

	os.system('sed -i "s/mpif90 -f90/mpif90 -fc/" configure.wps')
	
	print('[Notice]: Compile WPS ...')
	os.system('./compile > compile.out 2>&1')

	if check_build_result(('geogrid/src/geogrid.exe', 'metgrid/src/metgrid.exe', 'ungrib/src/ungrib.exe')):
		print('[Notice]: Succeeded.')
	else:
		print('[Error]: Failed! Check {}/compile.out'.format(args.wps_root))
		os.chdir(owd)
		exit(1)
else:
	print('[Notice]: WPS is already built.')

os.chdir(owd)
