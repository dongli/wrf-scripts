#!/usr/bin/env python3

import argparse
import re
import os
import pexpect
import platform
import sys
import subprocess
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import edit_file, run, cli, check_files

def build_wrf(wrf_root, wps_root, wrfplus_root, wrfda_root, args):
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
		cli.error('JASPERINC and JASPERLIB environment variables are not set!')

	os.chdir(wrf_root)
	if args.force: run('./clean -a &> /dev/null')
	expected_exe_files = ('main/wrf.exe', 'main/real.exe', 'main/ndown.exe', 'main/tc.exe')
	if not check_files(expected_exe_files):
		cli.notice('Configure WRF ...')
		if args.use_grib:
			cli.notice('Set GRIB2 flag.')
			edit_file('./arch/Config.pl', [
				['\$I_really_want_to_output_grib2_from_WRF = "FALSE"', '$I_really_want_to_output_grib2_from_WRF = "TRUE"']
			])
		if args.use_hyb:
			child = pexpect.spawn('./configure -hyb', encoding='utf-8')
		else:
			child = pexpect.spawn('./configure', encoding='utf-8')
		child.expect('Enter selection.*')
		if platform.system() == 'Darwin':
			if args.compiler_suite == 'gnu':
				child.sendline('15')
		else:
			if args.compiler_suite == 'intel':
				child.sendline('15')
			elif args.compiler_suite == 'gnu':
				child.sendline('34')
			elif args.compiler_suite == 'pgi':
				child.sendline('54')
		child.expect('Compile for nesting.*:')
		child.sendline('1')
		if platform.system() == 'Darwin': child.expect('This build of WRF will use NETCDF4 with HDF5 compression')
		child.wait()

		if args.compiler_suite == 'pgi':
			edit_file('./configure.wrf', [
				['pgf90', 'pgfortran'],
				['mpif90', 'mpifort']
			])

		cli.notice('Compile WRF ...')
		if args.verbose:
			run('./compile em_real')
		else:
			run('./compile em_real &> compile.out')
		
		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wrf_root}/compile.out')
	else:
		cli.notice('WRF is already built.')

	os.chdir(wps_root)
	if args.force: run('./clean -a &> /dev/null')
	expected_exe_files = ('geogrid/src/geogrid.exe', 'metgrid/src/metgrid.exe', 'ungrib/src/ungrib.exe')
	if not check_files(expected_exe_files):
		cli.notice('Configure WPS ...')
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

		run('sed -i "s/mpicc -cc=.*/mpicc/" configure.wps')
		run('sed -i "s/mpif90 -f90=.*/mpif90/" configure.wps')
		run('sed -i "s/WRF_DIR\s*=.*/WRF_DIR = ..\/WRF/" configure.wps')

		cli.notice('Compile WPS ...')
		if args.verbose:
			run('./compile')
		else:
			run('./compile &> compile.out')

		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wps_root}/compile.out')
	else:
		cli.notice('WPS is already built.')

	os.chdir(wrfplus_root)
	if args.force: run('./clean -a &> /dev/null')
	expected_exe_files = ('main/wrfplus.exe')
	if not check_files(expected_exe_files):
		cli.notice('Configure WRFPLUS ...')
		child = pexpect.spawn('./configure wrfplus')
		child.expect('Enter selection.*')
		if args.compiler_suite == 'intel':
			child.sendline('34')
		elif args.compiler_suite == 'gnu':
			child.sendline('18')
		elif args.compiler_suite == 'pgi':
			child.sendline('28')
		child.wait()

		cli.notice('Compile WRFPLUS ...')
		if args.verbose:
			run('./compile wrfplus')
		else:
			run('./compile wrfplus &> compile.wrfvar.out')

		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wrfplus_root}/compile.out')
	else:
		cli.notice('WRFPLUS is already built.')

	os.chdir(wrfda_root)
	if args.force: run('./clean -a &> /dev/null')
	expected_exe_files = (
		'var/build/da_advance_time.exe',
		'var/build/da_bias_airmass.exe',
		'var/build/da_bias_scan.exe',
		'var/build/da_bias_sele.exe',
		'var/build/da_bias_verif.exe',
		'var/build/da_rad_diags.exe',
		'var/build/da_tune_obs_desroziers.exe',
		'var/build/da_tune_obs_hollingsworth1.exe',
		'var/build/da_tune_obs_hollingsworth2.exe',
		'var/build/da_update_bc_ad.exe',
		'var/build/da_update_bc.exe',
		'var/build/da_verif_grid.exe',
		'var/build/da_verif_obs.exe',
		'var/build/da_wrfvar.exe',
		'var/build/gen_be_addmean.exe',
		'var/build/gen_be_cov2d3d_contrib.exe',
		'var/build/gen_be_cov2d.exe',
		'var/build/gen_be_cov3d2d_contrib.exe',
		'var/build/gen_be_cov3d3d_bin3d_contrib.exe',
		'var/build/gen_be_cov3d3d_contrib.exe',
		'var/build/gen_be_cov3d.exe',
		'var/build/gen_be_diags.exe',
		'var/build/gen_be_diags_read.exe',
		'var/build/gen_be_ensmean.exe',
		'var/build/gen_be_ensrf.exe',
		'var/build/gen_be_ep1.exe',
		'var/build/gen_be_ep2.exe',
		'var/build/gen_be_etkf.exe',
		'var/build/gen_be_hist.exe',
		'var/build/gen_be_stage0_gsi.exe',
		'var/build/gen_be_stage0_wrf.exe',
		'var/build/gen_be_stage1_1dvar.exe',
		'var/build/gen_be_stage1.exe',
		'var/build/gen_be_stage1_gsi.exe',
		'var/build/gen_be_stage2_1dvar.exe',
		'var/build/gen_be_stage2a.exe',
		'var/build/gen_be_stage2.exe',
		'var/build/gen_be_stage2_gsi.exe',
		'var/build/gen_be_stage3.exe',
		'var/build/gen_be_stage4_global.exe',
		'var/build/gen_be_stage4_regional.exe',
		'var/build/gen_be_vertloc.exe',
		'var/build/gen_mbe_stage2.exe',
		'var/obsproc/src/obsproc.exe')
	if not check_files(expected_exe_files):
		cli.notice('Configure WRFDA ...')
		child = pexpect.spawn('./configure wrfda')
		child.expect('Enter selection.*')
		if args.compiler_suite == 'intel':
			child.sendline('15')
		elif args.compiler_suite == 'gnu':
			child.sendline('34')
		elif args.compiler_suite == 'pgi':
			child.sendline('54')
		child.wait()

		cli.notice('Compile WRFDA ...')
		if args.verbose:
			run('./compile all_wrfvar')
		else:
			run('./compile all_wrfvar &> compile.wrfvar.out')

		if check_files(expected_exe_files, fatal=True):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wrfda_root}/compile.out')
	else:
		cli.notice('WRFDA is already built.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRFV3, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3 or WRF)')
	parser.add_argument(      '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument(      '--wrfplus-root', dest='wrfplus_root', help='WRFPLUS root directory (e.g. WRFPLUS)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
	parser.add_argument('-b', '--use-hyb', dest='use_hyb', help='Use hybrid vertical coordinate', action='store_true')
	parser.add_argument('-g', '--use-grib', dest='use_grib', help='Use GRIB IO capability of WRF', action='store_true')
	parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'])
	parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

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

	if not args.wps_root:
		if os.getenv('WPS_ROOT'):
			args.wps_root = os.getenv('WPS_ROOT')
		elif args.codes:
			args.wps_root = args.codes + '/WPS'
		else:
			cli.error('Option --wps-root or environment variable WPS_ROOT need to be set!')
	args.wps_root = os.path.abspath(args.wps_root)
	if not os.path.isdir(args.wps_root):
		cli.error(f'Directory {args.wps_root} does not exist!')

	if not args.wrfplus_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfplus_root = os.getenv('WRFPLUS_ROOT')
		elif args.codes:
			args.wrfplus_root = args.codes + '/WRFPLUS'
		else:
			cli.error('Option --wrfplus-root or environment variable WRFDA_ROOT need to be set!')
	args.wrfplus_root = os.path.abspath(args.wrfplus_root)
	if not os.path.isdir(args.wrfplus_root):
		cli.error(f'Directory {args.wrfplus_root} does not exist!')

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

	build_wrf(args.wrf_root, args.wps_root, args.wrfplus_root, args.wrfda_root, args)
