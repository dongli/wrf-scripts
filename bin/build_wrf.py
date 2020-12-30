#!/usr/bin/env python3

import argparse
import re
import os
import pexpect
import platform
import sys
import subprocess
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import wrf_version, Version, edit_file, run, cli, check_files

def build_wrf(wrf_root, wps_root, wrfplus_root, wrfda_root, args):
	if not 'HDF5' in os.environ:
		res = subprocess.run(['which', 'h5dump'], stdout=subprocess.PIPE)
		if res.returncode == 0:
			os.environ['HDF5'] = os.path.dirname(os.path.dirname(res.stdout.decode('utf-8')))
			cli.notice(f'Set HDF5 to {os.environ["HDF5"]}')
	if not 'HDF5' in os.environ:
		cli.warning('HDF5 environment variable is not set')

	if not 'NETCDF' in os.environ:
		res = subprocess.run(['which', 'nf-config'], stdout=subprocess.PIPE)
		if res.returncode == 0:
			os.environ['NETCDF'] = os.path.dirname(os.path.dirname(res.stdout.decode('utf-8')))
			res = subprocess.run(['nf-config', '--includedir'], stdout=subprocess.PIPE)
			os.environ['NETCDF_INC'] = res.stdout.decode('utf-8').strip()
			res = subprocess.run(['nf-config', '--flibs'], stdout=subprocess.PIPE)
			os.environ['NETCDF_LIB'] = re.search(r'-L([^ ]*)', res.stdout.decode('utf-8'))[1]
			cli.notice(f'Set NETCDF_INC to {os.environ["NETCDF_INC"]}')
			cli.notice(f'Set NETCDF_LIB to {os.environ["NETCDF_LIB"]}')
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

	if not 'LIBPNG_ROOT' in os.environ:
		cli.warning('LIBPNG_ROOT environment variable is not set. Library PNG may not be found!')

	if not 'WRFIO_NCD_LARGE_FILE_SUPPORT' in os.environ:
		os.environ['WRFIO_NCD_LARGE_FILE_SUPPORT'] = '1'
		cli.notice('Set WRFIO_NCD_LARGE_FILE_SUPPORT to 1.')

	if args.rttov:
		os.environ['RTTOV'] = args.rttov
		cli.notice(f'Use RTTOV in {args.rttov}.')

	# ---------------------------------------------------------------------------------
	#                                    WRF
	os.chdir(wrf_root)
	version = wrf_version(wrf_root)
	if version <= Version('3.6.1'):
		os.environ['BUFR'] = '1'
	# Fix possible code bugs.
	if Version('3.6.1') <= version <= Version('3.8.1'):
		edit_file('phys/module_cu_g3.F', [['integer,  dimension \(12\) :: seed', 'integer,  dimension (33) :: seed']])
	if args.force: run('./clean -a 1> /dev/null 2>&1')
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
				if args.openmp:
					child.sendline('16') # INTEL (ifort/icc) dm+sm
				else:
					child.sendline('15') # INTEL (ifort/icc) dmpar
			elif args.compiler_suite == 'gnu':
				if args.openmp:
					child.sendline('35') # GNU (gfortran/gcc) dm+sm
				else:
					child.sendline('34') # GNU (gfortran/gcc) dmpar
			elif args.compiler_suite == 'pgi':
				if args.openmp:
					child.sendline('55') # PGI (pgf90/pgcc) dm+sm
				else:
					child.sendline('54') # PGI (pgf90/pgcc) dmpar
		child.expect('Compile for nesting.*:')
		child.sendline('1')
		if platform.system() == 'Darwin': child.expect('This build of WRF will use NETCDF4 with HDF5 compression')
		child.wait()

		if args.compiler_suite == 'intel':
			edit_file('./configure.wrf', [
				['mpif90', 'mpiifort'],
				['mpicc', 'mpiicc']
			])
		elif args.compiler_suite == 'pgi':
			edit_file('./configure.wrf', [
				['pgf90', 'pgfortran'],
				['mpif90', 'mpifort']
			])

		# Fix for OpenMPI.
		edit_file('./configure.wrf', [
			['DM_CC\s*=\s*mpicc\s*$', 'DM_CC = mpicc -DMPI2_SUPPORT\n']
		])

		cli.notice('Compile WRF ...')
		if args.debug:
			if args.compiler_suite == 'intel':
				debug_options = '-O0 -g -traceback'
			elif args.compiler_suite == 'gnu':
				debug_options = '-O0 -g -fbacktrace'
			edit_file('configure.wrf', [
				['FCFLAGS\s*=\s*\$\(FCOPTIM\)\s*\$\(FCBASEOPTS\)', f'FCFLAGS = {debug_options} $(FCBASEOPTS)']
			])
		if args.verbose:
			run(f'./compile em_real')
		else:
			run(f'./compile em_real 1> compile.out 2>&1')
		
		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wrf_root}/compile.out')
	else:
		cli.notice('WRF is already built.')

	# ---------------------------------------------------------------------------------
	#                                    WPS
	os.chdir(wps_root)
	if args.force: run('./clean -a 1> /dev/null 2>&1')
	expected_exe_files = ('geogrid/src/geogrid.exe', 'metgrid/src/metgrid.exe', 'ungrib/src/ungrib.exe')
	if not check_files(expected_exe_files):
		cli.notice('Configure WPS ...')
		child = pexpect.spawn('./configure')
		child.expect('Enter selection.*')
		if args.compiler_suite == 'intel':
			child.sendline('19') # Linux x86_64, Intel compiler    (dmpar)
		elif args.compiler_suite == 'gnu':
			child.sendline('3')  # Linux x86_64, gfortran    (dmpar)
		elif args.compiler_suite == 'pgi':
			child.sendline('7')
		child.wait()

		if args.compiler_suite == 'intel':
			edit_file('./configure.wps', [
				['mpif90', 'mpiifort'],
				['mpicc', 'mpiicc']
			])
		elif args.compiler_suite == 'pgi':
			edit_file('./configure.wps', [
				['pgf90', 'pgfortran'],
				['mpif90', 'mpifort']
			])
		else:
			run('sed -i "s/mpicc -cc=.*/mpicc/" configure.wps')
			run('sed -i "s/mpif90 -f90=.*/mpif90/" configure.wps')

		run('sed -i "s/WRF_DIR\s*=.*/WRF_DIR = ..\/WRF/" configure.wps')
		if 'LIBPNG_ROOT' in os.environ:
			run(f'sed -i "s@COMPRESSION_LIBS\s*=\(.*\)@COMPRESSION_LIBS = \\1 -L{os.environ["LIBPNG_ROOT"]}/lib@" configure.wps')
			run(f'sed -i "s@COMPRESSION_INC\s*=\(.*\)@COMPRESSION_INC = \\1 -I{os.environ["LIBPNG_ROOT"]}/include@" configure.wps')

		if args.compiler_suite == 'gnu':
			# Fix for gfortran 9.1.0.
			edit_file('ungrib/src/ngl/g2/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_8)/=0']], return_on_first_match=True)
			edit_file('ungrib/src/ngl/g2/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_4)/=0']], return_on_first_match=True)
			edit_file('ungrib/src/ngl/g2/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_2)/=0']], return_on_first_match=True)
			edit_file('ungrib/src/ngl/g2/intmath.f', [['iand\(i,i-1\)/=0', 'iand(i,i-1_1)/=0']], return_on_first_match=True)

		# Fix for OpenMPI.
		edit_file('./configure.wps', [
			['DM_CC\s*=\s*mpicc\s*$', 'DM_CC = mpicc -DMPI2_SUPPORT\n']
		])

		cli.notice('Compile WPS ...')
		if args.verbose:
			run('./compile')
		else:
			run('./compile 1> compile.out 2>&1')

		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wps_root}/compile.out')
	else:
		cli.notice('WPS is already built.')

	# ---------------------------------------------------------------------------------
	#                                    WRFPLUS
	os.chdir(wrfplus_root)
	if args.force: run('./clean -a 1> /dev/null 2>&1')
	if Version('3.6.1') <= version <= Version('3.8.1'):
		edit_file('phys/module_cu_g3.F', [['integer,  dimension \(12\) :: seed', 'integer,  dimension (33) :: seed']])
		if version == Version('3.6.1'):
			line_number = 841
		elif version == Version('3.8.1'):
			line_number = 855
		else:
			error('Find out the wrong OpenMP directive in WRFPLUS/main/module_wrf_top.F!')
		edit_file('main/module_wrf_top.F', [[line_number, '   !$OMP DEFAULT (SHARED) PRIVATE ( ij )\n']])
	if version >= Version('4.0'):
		expected_exe_files = ('main/wrfplus.exe')
	else:
		expected_exe_files = ('main/wrf.exe')
	if not check_files(expected_exe_files):
		cli.notice('Configure WRFPLUS ...')
		if args.use_grib:
			cli.notice('Set GRIB2 flag.')
			edit_file('./arch/Config.pl', [
				['\$I_really_want_to_output_grib2_from_WRF = "FALSE"', '$I_really_want_to_output_grib2_from_WRF = "TRUE"']
			])
		child = pexpect.spawn('./configure wrfplus')
		child.expect('Enter selection.*')
		if args.compiler_suite == 'intel':
			if version <= Version('3.6.1'):
				child.sendline('8')
			else:
				child.sendline('34')
		elif args.compiler_suite == 'gnu':
			child.sendline('18')
		elif args.compiler_suite == 'pgi':
			child.sendline('28')
		child.wait()

		if args.compiler_suite == 'intel':
			edit_file('./configure.wrf', [
				['mpif90', 'mpiifort'],
				['mpicc', 'mpiicc'],
				['override-limits', 'qoverride-limits']
			])

		# Fix for OpenMPI.
		edit_file('./configure.wrf', [
			['DM_CC\s*=\s*mpicc\s*$', 'DM_CC = mpicc -DMPI2_SUPPORT\n']
		])

		cli.notice('Compile WRFPLUS ...')
		if args.debug:
			if args.compiler_suite == 'intel':
				debug_options = '-O0 -g -traceback'
			elif args.compiler_suite == 'gnu':
				debug_options = '-O0 -g -fbacktrace'
			edit_file('configure.wrf', [
				['FCFLAGS\s*=\s*\$\(FCOPTIM\)\s*\$\(FCBASEOPTS\)', f'FCFLAGS = {debug_options} $(FCBASEOPTS)']
			])
		if version >= Version('4.0'):
			build_target = 'wrfplus'
		else:
			build_target = 'wrf'
		if args.verbose:
			run(f'./compile {build_target}')
		else:
			run(f'./compile {build_target} 1> compile.out 2>&1')

		if check_files(expected_exe_files):
			cli.notice('Succeeded.')
		else:
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check {wrfplus_root}/compile.out')
	else:
		cli.notice('WRFPLUS is already built.')

	# ---------------------------------------------------------------------------------
	#                                    WRFDA
	os.chdir(wrfda_root)
	os.environ['WRFPLUS_DIR'] = wrfplus_root
	if args.force: run('./clean -a 1> /dev/null 2>&1')
	if Version('3.6.1') <= version <= Version('3.9.1'):
		cli.warning(f'Fix {wrfda_root}/var/da/da_define_structures/da_zero_y.inc')
		edit_file('var/da/da_define_structures/da_zero_y.inc', [
			[', value \)', ', value_ )'],
			[':: value$', ':: value_\nreal value'],
			['if \(.not.\(present\(value\)\)\) value = 0.0', '''
   if (.not.(present(value_))) then
      value = 0.0
   else
      value = value_
   end if
''']
		])
	if version == Version('4.1.1'):
		cli.warning(f'Fix {wrfda_root}/share/input_wrf.F')
		edit_file('share/input_wrf.F', [
			['FUNCTION check_which_switch', 'FUNCTION check_which_switch1']
		])
	expected_exe_files = [
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
		'var/obsproc/src/obsproc.exe']
	if not check_files(expected_exe_files):
		cli.notice('Configure WRFDA ...')
		if args.use_grib:
			cli.notice('Set GRIB2 flag.')
			edit_file('./arch/Config.pl', [
				['\$I_really_want_to_output_grib2_from_WRF = "FALSE"', '$I_really_want_to_output_grib2_from_WRF = "TRUE"']
			])
		child = pexpect.spawn('./configure 4dvar')
		child.expect('Enter selection.*')
		if args.compiler_suite == 'intel':
			child.sendline('8')
		elif args.compiler_suite == 'gnu':
			child.sendline('18')
		elif args.compiler_suite == 'pgi':
			child.sendline('28')
		child.wait()

		if args.compiler_suite == 'intel':
			edit_file('./configure.wrf', [
				['mpif90', 'mpiifort'],
				['mpicc', 'mpiicc']
			])

		# Fix for OpenMPI.
		edit_file('./configure.wrf', [
			['DM_CC\s*=\s*mpicc\s*$', 'DM_CC = mpicc -DMPI2_SUPPORT\n']
		])

		cli.notice('Compile WRFDA ...')
		if args.debug:
			if args.compiler_suite == 'intel':
				debug_options = '-O0 -g -traceback'
			elif args.compiler_suite == 'gnu':
				debug_options = '-O0 -g -fbacktrace'
			edit_file('configure.wrf', [
				['FCFLAGS\s*=\s*\$\(FCOPTIM\)\s*\$\(FCBASEOPTS\)', f'FCFLAGS = {debug_options} $(FCBASEOPTS)']
			])
		if args.verbose:
			run(f'./compile all_wrfvar')
		else:
			run(f'./compile all_wrfvar 1> compile.out 2>&1')

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
	parser.add_argument(      '--openmp', help='Use OpenMP parallelism.', action='store_true')
	parser.add_argument('-j', '--jobs', help='Set job size to compile.', type=int, default=2)
	parser.add_argument(      '--rttov', help='Use RTTOV for satelliate DA.')
	parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'], required=True)
	parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
	parser.add_argument('-d', '--debug', help='Build WRF with debug compile options', action='store_true')
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
