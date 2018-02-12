#!/usr/bin/env python3.6

import argparse
import fileinput
import os
import pexpect
import re
from shutil import copyfile

parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument('-b', '--use-hyb', dest='use_hyb', help='Use hybrid vertical coordinate', action='store_true')
parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
args = parser.parse_args()

if not args.wrf_root and os.getenv('WRF_ROOT'):
	args.wrf_root = os.getenv('WRF_ROOT')
elif not args.wrf_root:
	print('[Error]: Option --wrf-root or environment variable WRF_ROOT need to be set!')
	exit(1)

if not args.wps_root and os.getenv('WPS_ROOT'):
	args.wps_root = os.getenv('WPS_ROOT')
elif not args.wps_root:
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
						print(change[1])
						found = True
						break
				if not found:
					print(line, end='')
	except Exception as e:
		print('[Error]: Failed to edit file {}! {}'.format(filepath, e))
		exit(1)

owd = os.getcwd()

os.chdir(args.wrf_root)
if args.force: os.system('./clean -a')
if not check_build_result(('main/wrf.exe', 'main/real.exe', 'main/ndown.exe', 'main/tc.exe')):
	# Fix bug when find netcdf.
	edit_file('./configure', [
		['if \[ -f "$NETCDF/lib/libnetcdff.a" -o -f "$NETCDF/lib/libnetcdff.so" \] ; then',
		 'if \[ -f "$NETCDF/lib64/libnetcdff.a" -o -f "$NETCDF/lib64/libnetcdff.so" -o -f "$NETCDF/lib/libnetcdff.a" -o -f "$NETCDF/lib/libnetcdff.so" \] ; then'],
		['if \[ -f "$NETCDF/lib/libnetcdf.a" -o -f "$NETCDF/lib/libnetcdf.so" \] ; then',
		 'if \[ -f "$NETCDF/lib64/libnetcdf.a" -o -f "$NETCDF/lib64/libnetcdf.so" -o -f "$NETCDF/lib/libnetcdf.a" -o -f "$NETCDF/lib/libnetcdf.so" \] ; then']
	])
	print('[Notice]: Configure WRF ...')
	if args.use_hyb:
		child = pexpect.spawn('./configure -hyb')
	else:
		child = pexpect.spawn('./configure')
	child.expect('Enter selection.*')
	child.sendline('34')
	child.expect('Compile for nesting.*')
	child.sendline('1')
	child.wait()
	
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
if args.force: os.system('./clean -a')
if not check_build_result(('geogrid/src/geogrid.exe', 'metgrid/src/metgrid.exe', 'ungrib/src/ungrib.exe')):
	# Fix bug when find netcdf.
	edit_file('./configure', [
		['if [ -f "$NETCDF/lib/libnetcdff.a" ] ; then',
		 'if [ -f "$NETCDF/lib/libnetcdff.a" -o -f "$NETCDF/lib64/libnetcdff.a" -o -f "$NETCDF/lib/libnetcdff.so" -o -f "$NETCDF/lib64/libnetcdff.so" ] ; then']
	])
	print('[Notice]: Configure WPS ...')
	child = pexpect.spawn('./configure')
	child.expect('Enter selection.*')
	child.sendline('3')
	child.wait()

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
