#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
from netCDF4 import Dataset
import re
from shutil import copyfile
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, submit_job, parse_config

def run_real(work_root, wps_work_dir, wrf_root, config, args):
	start_time = config['custom']['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)
	max_dom = config['domains']['max_dom']

	if not os.path.isdir(wps_work_dir): cli.error(f'WPS work directory {wps_work_dir} does not exist!')
	wrf_work_dir = os.path.abspath(work_root) + '/wrf'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	cli.stage(f'Run real.exe at {wrf_work_dir} ...')
	expected_files = ['wrfinput_d{:02d}_{}'.format(i + 1, start_time_str) for i in range(max_dom)]
	if not check_files(expected_files) or args.force:
		run('rm -f wrfinput_* met_em.*.nc')
		run(f'ln -s {wps_work_dir}/met_em.*.nc .')
		try:
			dataset = Dataset(glob('met_em.*.nc')[0])
		except:
			cli.error('Failed to open one of met_em.*.nc file!')
		namelist_input = f90nml.read('./namelist.input')
		namelist_input['domains']['num_metgrid_levels'] = dataset.dimensions['num_metgrid_levels'].size
		namelist_input['physics']['num_land_cat'] = dataset.getncattr('NUM_LAND_CAT')
		if 'num_st_layers' in dataset.dimensions:
			namelist_input['domains']['num_metgrid_soil_levels'] = dataset.dimensions['num_st_layers'].size
		else:
			cli.warning(f'Dimension num_st_layers is not in {dataset.filepath()}! Set num_metgrid_soil_levels to 0.')
			namelist_input['domains']['num_metgrid_soil_levels'] = 0
		dataset.close()
		namelist_input.write('./namelist.input', force=True)
		submit_job(f'{wrf_root}/run/real.exe', args.np, config, args, wait=True)
		for i in range(max_dom):
			if not os.path.isfile('wrfinput_d{0:02d}'.format(i + 1)):
				cli.error(f'Failed to generate wrfinput_d{0:02d}! See {wrf_work_dir}/rsl.error.0000.'.format(i + 1))
			run('mv wrfinput_d{0:02d} wrfinput_d{0:02d}_{1}'.format(i + 1, start_time_str))
		if os.path.isfile('wrfbdy_d01'):
			run(f'mv wrfbdy_d01 wrfbdy_d01_{start_time_str}')
		cli.notice('Succeeded.')
	else:
		run('ls -l wrfinput_* wrfbdy_* 2> /dev/null')
		cli.notice('File wrfinput_* already exist.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument(      '--wps-work-dir',  dest='wps_work_dir', help='Work root directory of WPS')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file')
	parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs.', action='store_true')
	parser.add_argument(      '--pbs', help='Use PBS job management system variants (e.g. TORQUE) to run MPI jobs.', action='store_true')
	parser.add_argument(      '--ntasks-per-node', dest='ntasks_per_node', help='Override the default setting.', default=None, type=int)
	parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
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

	if not args.wps_work_dir:
		args.wps_work_dir = args.work_root + '/wps'
	if not os.path.isdir(args.wps_work_dir):
		cli.error(f'Directory {args.wps_work_dir} does not exist!')
	args.wps_work_dir = os.path.abspath(args.wps_work_dir)

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

	config = parse_config(args.config_json)

	run_real(args.work_root, args.wps_work_dir, args.wrf_root, config, args)

