#!/usr/bin/env python3

import argparse
import re
import os
import pexpect
import subprocess
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import gsi_version, Version, edit_file, run, cli, check_files

def build_gsi(wrf_root, gsi_root, args):
	# Check environment.
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

	if not os.getenv('LAPACK_PATH') and args.compiler_suite != 'intel':
		cli.error('Shell variable LAPACK_PATH is not set!')

	version = gsi_version(args.gsi_root)

	if version <= Version('3.6'):
		# 3.7 changes: Added wrf interface as a library (wrflib). No need to compile WRF with GSI and EnKF.
		if not os.path.isdir(args.wrf_root):
			cli.error(f'WRF directory {args.wrf_root} does not exist!')
		os.chdir(args.wrf_root)
		expected_exe_files = ('main/wrf.exe', 'main/real.exe', 'main/ndown.exe', 'main/tc.exe')
		if not check_files(expected_exe_files):
			cli.error('WRF has not been built! Build it first.')

	os.chdir(args.gsi_root)

	if args.force: run('rm -rf build')
	if not os.path.isdir('build'): os.mkdir('build')
	os.chdir('build')
	if version == Version('3.6'):
		expected_exe_files = (
			'bin/gsi.x',
			'lib/libbacio_v2.0.1.a',
			'lib/libbufr_v10.2.5.a',
			'lib/libcrtm_v2.2.3.a',
			'lib/libenkfdeplib.a',
			'lib/libenkflib.a',
			'lib/libgsilib_shrd.a',
			'lib/libgsilib_wrf.a',
			'lib/libnemsio_v2.2.1.a',
			'lib/libsfcio_v1.1.0.a',
			'lib/libsigio_v2.0.1.a',
			'lib/libsp_v2.0.2.a',
			'lib/libw3emc_v2.2.0.a',
			'lib/libw3nco_v2.0.6.a'
		)
	elif version == Version('3.7'):
		expected_exe_files = (
			'bin/enkf_wrf.x',
			'bin/gsi.x',
			'lib/libbacio_v2.0.1.a',
			'lib/libbufr_v10.2.5.a',
			'lib/libcrtm_v2.2.3.a',
			'lib/libenkfdeplib.a',
			'lib/libenkflib.a',
			'lib/libgsilib_shrd.a',
			'lib/libgsilib_wrf.a',
			'lib/libnemsio_v2.2.1.a',
			'lib/libsfcio_v1.1.0.a',
			'lib/libsigio_v2.0.1.a',
			'lib/libsp_v2.0.2.a',
			'lib/libw3emc_v2.2.0.a',
			'lib/libw3nco_v2.0.6.a'
		)
	if not check_files(expected_exe_files):
		cmake_args = f'-DBUILD_ENKF=ON -DBUILD_CORELIBS=ON -DUSE_WRF=ON -DBUILD_WRF=ON -DBUILD_GFS=OFF'
		if version == Version('3.6'):
			cli.notice('Fix GSI 3.6!')
			edit_file('../cmake/Modules/FindCORELIBS.cmake', [
				['\${CMAKE_SOURCE_DIR}/libsrc', '${CMAKE_SOURCE_DIR}/lib/libsrc']
			])
			if args.compiler_suite == 'gnu':
				edit_file('../cmake/Modules/setCompilerFlags.cmake', [
					['set\(BACIO_Fortran_FLAGS " -O3 -fconvert=big-endian -ffree-form', 'set(BACIO_Fortran_FLAGS " -O3 -fconvert=big-endian']
				])
			elif args.compiler_suite == 'intel':
				edit_file('../cmake/Modules/setCompilerFlags.cmake', [
					['set \(BACIO_Fortran_FLAGS "-O3 -free -assume nocc_omp', 'set(BACIO_Fortran_FLAGS " -O3 -assume nocc_omp']
				])
			edit_file('../core-libs/sigio/CMakeLists.txt', [
				['\*\.f\)', '*.f90)']
			])
			edit_file('../src/hybrid_ensemble_isotropic.F90', [
				['stop\(123\)', 'stop 123']
			])
			edit_file('../src/setupoz.f90', [
				['my_head%ij\(1\),my_head%wij\(1\)\)', 'my_head%ij,my_head%wij)']
			])
			cmake_args += f'-DWRFPATH={args.wrf_root}'
		if version == Version('3.7'):
			cli.notice('Fix GSI 3.7!')
			edit_file('../src/setuplight.f90', [
				['my_head%wij\(1\)\)', 'my_head%wij)']
			])
			cli.warning('GSI 3.7 has bug when rerun cmake, so clean all build files.')
			run('rm -rf ../build/*')
			cmake_args += '-DBUILD_UTIL_COM=ON'

		# Fix not-found -lnetcdf -lnetcdff.
		edit_file('../cmake/Modules/setCompilerFlags.cmake', [['-lnetcdf -lnetcdff', '']])

		cli.notice('Configure GSI ...')
		if args.compiler_suite == 'gnu':
			cc = 'gcc'; cxx = 'g++'; fc = 'gfortran'
		elif args.compiler_suite == 'intel':
			cc = 'mpiicc'; cxx = 'mpiicpc'; fc = 'mpiifort'
		if args.verbose:
			run(f'CC={cc} CXX={cxx} FC={fc} cmake .. {cmake_args}')
		else:
			run(f'CC={cc} CXX={cxx} FC={fc} cmake .. {cmake_args} &> cmake.out')
	
		cli.notice('Compile GSI ...')
		if args.verbose:
			run('make')
		else:
			run('make &> make.out')
	
		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed')
			else:
				cli.error(f'Failed! Check {args.gsi_root}/build/make.out')
	else:
		cli.notice('GSI has already been built.')

	if version == Version('3.6'):
		os.chdir(f'{args.gsi_root}/util/bufr_tools')
		if args.force: run('make clean')
		expected_exe_files = (
			'bufr_append_sample.exe',
			'bufr_decode_radiance.exe',
			'bufr_decode_sample.exe',
			'bufr_encode_sample.exe',
			'prepbufr_append_retrieve.exe',
			'prepbufr_append_surface.exe',
			'prepbufr_append_upperair.exe',
			'prepbufr_decode_all.exe',
			'prepbufr_encode_surface.exe',
			'prepbufr_encode_upperair.exe',
			'prepbufr_inventory.exe'
		)
		if not check_files(expected_exe_files):
			edit_file('makefile', [
				['^\s*FC\s*=.*$', f'FC = {fc}'],
				['-I\.\./\.\./dtc', '-I../../build'],
				['-L\.\./\.\./dtc', '-L../../build'],
				['-lbufr_i4r8', '-lbufr_v10.2.5']
			])
		
			cli.notice('Compile bufr_tools ...')
			if args.verbose:
				run('make')
			else:
				run('make &> make.out')
		
			if check_files(expected_exe_files):
				cli.notice('Succeeded.')
			else:
				if args.verbose:
					cli.error('Failed!')
				else:
					cli.error(f'Failed! Check {args.gsi_root}/util/bufr_tools/make.out')
		else:
			cli.notice('GSI bufr_tools has been built.')
		
		os.chdir(f'{args.gsi_root}/util/Analysis_Utilities/read_diag/')
		expected_exe_files = (
			'read_diag_conv.exe',
			'read_diag_conv_ens.exe',
			'read_diag_rad.exe'
		)
		if not check_files(expected_exe_files):
			edit_file('makefile', [
				['include \.\./\.\./\.\./dtc/configure.gsi', ''],
				['\$\(SFC\)', fc],
				['-I\.\./\.\./\.\./dtc', '-I../../../build'],
				['-L\.\./\.\./\.\./src -lgsi', '-L../../../build/lib -lgsilib_shrd'],
				['FLAGS= \$\(FFLAGS_DEFAULT\)', 'FLAGS = -fconvert=big-endian']
			])
		
			cli.notice('Compile read_diag ...')
			if args.verbose:
				run('make')
			else:
				run('make &> make.out')
		
			if check_files(expected_exe_files):
				cli.notice('Succeeded.')
			else:
				if args.verbose:
					cli.error('Failed')
				else:
					cli.error(f'Failed! Check {args.gsi_root}/util/Analysis_Utilities/read_diag/make.out')
		else:
			cli.notice('GSI read_diag has been built.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, GSI)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
	parser.add_argument(      '--gsi-root', dest='gsi_root', help='GSI root directory (e.g. GSI)')
	parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'])
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
	args = parser.parse_args()
	
	if not args.wrf_root:
		if os.getenv('WRF_ROOT'):
			args.wrf_root = os.getenv('WRF_ROOT')
		elif args.codes:
			args.wrf_root = args.codes + '/WRF'
	if args.wrf_root: args.wrf_root = os.path.abspath(args.wrf_root)

	if not args.gsi_root:
		if os.getenv('GSI_ROOT'):
			args.gsi_root = os.getenv('GSI_ROOT')
		elif args.codes:
			args.gsi_root = args.codes + '/GSI'
		else:
			cli.error('Option --gsi-root or environment variable GSI_ROOT need to be set!')
	args.gsi_root = os.path.abspath(args.gsi_root)
	if not os.path.isdir(args.gsi_root):
		cli.error(f'Directory {args.gsi_root} does not exist!')

	build_gsi(args.wrf_root, args.gsi_root, args)

