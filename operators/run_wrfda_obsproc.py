#! /usr/bin/env python3

import argparse
from glob import glob
from netCDF4 import Dataset 
import os
import re
import pendulum
import f90nml
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/../utils')
from utils import cli, check_files, run, parse_config, submit_job, has_key, get_value

def run_wrfda_obsproc(work_root, wrfda_root, littler_root, config, args):
	start_time = config['custom']['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)

	wrf_work_dir = os.path.abspath(work_root) + '/wrf'

	wrfda_work_dir = os.path.abspath(work_root) + '/wrfda/obsproc'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	cli.notice('Use builtin obserr.')
	run(f'ln -sf {wrfda_root}/var/obsproc/obserr.txt {wrfda_work_dir}')

	# Use d01 domain extent.
	if check_files([f'{wrf_work_dir}/wrfinput_d01_{start_time_str}']):
		ncfile       = Dataset(f'{wrf_work_dir}/wrfinput_d01_{start_time_str}', 'r')
		iproj        = ncfile.getncattr('MAP_PROJ')
		phic         = ncfile.getncattr('CEN_LAT')
		xlonc        = ncfile.getncattr('CEN_LON')
		moad_cen_lat = ncfile.getncattr('MOAD_CEN_LAT')
		standard_lon = ncfile.getncattr('STAND_LON')
		ncfile.close()
	else:
		iproj        = config['geogrid']['map_proj']
		phic         = config['geogrid']['ref_lat']
		xlonc        = config['geogrid']['ref_lon']
		moad_cen_lat = config['geogrid']['ref_lat']
		standard_lon = config['geogrid']['ref_lon']

	output_format = get_value(config, 'custom', 'obsproc', 'output_format', default=2)
	time_window   = get_value(config, 'custom', 'da', 'time_window', default=360)

	if has_key(config, ('custom', 'da', 'type')):
		if config['custom']['da']['type'] == '3dvar':
			namelist_obsproc = f90nml.read(f'{wrfda_root}/var/obsproc/namelist.obsproc.3dvar.wrfvar-tut')
		else:
			cli.error('Currently, we only support 3DVar...')
	else:
		namelist_obsproc = f90nml.read(f'{wrfda_root}/var/obsproc/namelist.obsproc.3dvar.wrfvar-tut')
	namelist_obsproc['record1']['obs_gts_filename' ] = 'obs.gts.{}'.format(start_time.format('YYYYMMDDHHmm'))
	namelist_obsproc['record2']['time_window_min'  ] = start_time.subtract(minutes=time_window/2).format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record2']['time_analysis'    ] = start_time.format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record2']['time_window_max'  ] = start_time.add(minutes=time_window/2).format('YYYY-MM-DD_HH:mm:ss')
	namelist_obsproc['record3']['max_number_of_obs'] = 1200000
	namelist_obsproc['record7']['PHIC'             ] = phic
	namelist_obsproc['record7']['XLONC'            ] = xlonc
	namelist_obsproc['record7']['MOAD_CEN_LAT'     ] = moad_cen_lat
	namelist_obsproc['record7']['STANDARD_LON'     ] = standard_lon
	namelist_obsproc['record8']['NESTIX'           ] = config['geogrid']['e_sn']
	namelist_obsproc['record8']['NESTJX'           ] = config['geogrid']['e_we']
	namelist_obsproc['record8']['DIS'              ] = config['geogrid']['dx']
	namelist_obsproc['record9']['OUTPUT_OB_FORMAT' ] = output_format
	namelist_obsproc.write('./namelist.obsproc', force=True)

	cli.stage(f'Run obsproc.exe at {wrfda_work_dir} ...')
	expected_files = [f'obs_gts_{start_time.format("YYYY-MM-DD_HH:mm:ss")}.3DVAR']
	if not check_files(expected_files) or args.force:
		run('rm -f obs_gts_*')
		if os.path.exists(f'{littler_root}/{start_time.format("YYYYMMDD")}/obs.gts.{start_time.format("YYYYMMDDHHmm")}'):
			run(f'ln -sf {littler_root}/{start_time.format("YYYYMMDD")}/obs.gts.{start_time.format("YYYYMMDDHHmm")} {wrfda_work_dir}')
		else:
			cli.error(f'Failed! {littler_root}/{start_time.format("YYYYMMDD")}/obs.gts.{start_time.format("YYYYMMDDHHmm")} Not Found.')
		submit_job(f'{wrfda_root}/var/obsproc/obsproc.exe', 1, config, args, wait=True)
		if not check_files(expected_files):
			cli.error(f'Failed!')
		cli.notice('Succeeded.')
	else:
		cli.notice('File obs_gts_* already exist.')
	run('ls -l obs_gts_*')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRFDA obsproc tool.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS, WRFDA)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')	
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-l', '--littler-root', dest='littler_root', help='Little_r data root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs.', action='store_true')
	parser.add_argument(      '--pbs', help='Use PBS job management system variants (e.g. TORQUE) to run MPI jobs.', action='store_true')
	parser.add_argument(      '--ntasks-per-node', dest='ntasks_per_node', help='Override the default setting.', default=None, type=int)
	parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=1, type=int)
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	args = parser.parse_args()

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or environment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

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

	if not args.littler_root:
		if os.getenv('LITTLER_ROOT'):
			args.littler_root = os.getenv('LITTLER_ROOT')
		else:
			cli.error('Option --littler-root or environment variable LITTLER_ROOT need to be set!')
	args.littler_root = os.path.abspath(args.littler_root)
	if not os.path.isdir(args.littler_root):
		cli.error(f'Directory {args.littler_root} does not exist!')

	config = parse_config(args.config_json)

	run_wrfda_obsproc(args.work_root, args.wrfda_root, args.littler_root, config, args)
