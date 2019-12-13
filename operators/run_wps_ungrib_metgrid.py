#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
from jinja2 import Template
import re
from shutil import copy
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, check_files, wrf_version, Version, run, submit_job, parse_config, has_key, get_value

def run_wps_ungrib_metgrid(work_root, wps_root, bkg_root, config, args):
	start_time = config['custom']['start_time']

	bkg_type = get_value(config['custom'], ['background', 'type'], default='gfs')
	if bkg_type == 'gfs' and not has_key(config['custom'], ['background', 'file_pattern']):
		config['custom']['background']['file_pattern'] = 'gfs.t{{ bkg_start_time.format("HH") }}z.pgrb2.*.f{{ "%03d" % bkg_forecast_hour }}'

	wps_work_dir = os.path.abspath(work_root) + '/wps'
	if not os.path.isdir(wps_work_dir):
		cli.error(f'Directory {wps_work_dir} does not exist! Run GEOGRID first.')
	os.chdir(wps_work_dir)

	version = wrf_version(wps_root)

	if start_time >= pendulum.datetime(2019, 6, 11) and version < Version('4.0'):
		cli.error('WPS (>= 4.0) is needed to process new GFS data since 2019-06-12!')

	cli.stage(f'Run ungrib.exe at {wps_work_dir} ...')
	if has_key(config['custom'], ['background', 'vtable']):
		if os.path.isfile(config["custom"]["background"]["vtable"]):
			run(f'ln -sf {config["custom"]["Background"]["vtable"]} {wps_work_dir}/Vtable')
		else:
			run(f'ln -sf {wps_root}/ungrib/Variable_Tables/Vtable.{config["custom"]["background"]["vtable"]} {wps_work_dir}/Vtable')
	elif bkg_type.lower() == 'era5':
		run(f'ln -sf {wps_root}/ungrib/Variable_Tables/Vtable.ERA-interim.pl {wps_work_dir}/Vtable')
	else:
		run(f'ln -sf {wps_root}/ungrib/Variable_Tables/Vtable.{bkg_type.upper()} {wps_work_dir}/Vtable')

	def eval_bkg_dir(bkg_start_time, bkg_time):
		if has_key(config['custom'], ['background', 'dir_pattern']):
			return bkg_root + '/' + Template(config['custom']['background']['dir_pattern']).render(bkg_start_time=bkg_start_time, bkg_time=bkg_time)
		elif bkg_type == 'gfs':
			return bkg_root + '/gfs.' + bkg_start_time.format('YYYYMMDD') + '/' + bkg_start_time.format('HH')

	# Find out suitable background data that cover forecast time period.
	def is_bkg_exist(bkg_start_time):
		bkg_dir = eval_bkg_dir(bkg_start_time, bkg_start_time)
		if has_key(config['custom'], ['background', 'file_pattern']):
			if type(config['custom']['background']['file_pattern']) == list:
				file_pattern = config['custom']['background']['file_pattern'][0]
			else:
				file_pattern = config['custom']['background']['file_pattern']
			file_name = Template(file_pattern).render(bkg_start_time=bkg_start_time, bkg_time=bkg_start_time, bkg_forecast_hour=0)
		elif bkg_type == 'gfs':
			file_name = 'gfs.t{:02d}z.pgrb2.*.f*'.format(bkg_start_time.hour)
		return len(glob(f'{bkg_dir}/{file_name}')) != 0

	found = False
	for date in (start_time, start_time.subtract(days=1)):
		if found: break
		for hour in (18, 12, 6, 0):
			bkg_start_time = pendulum.datetime(date.year, date.month, date.day, hour)
			if ((start_time - date).days == 1 or start_time.hour >= hour) and is_bkg_exist(bkg_start_time):
				found = True
				break
	if not found: cli.error('Background data is not available!')
	cli.notice(f'Use background starting from {bkg_start_time}.')

	# Generate the background times.
	interval_seconds = int(re.search('interval_seconds\s*=\s*(\d+)', open('./namelist.wps').read())[1])
	bkg_times = []
	bkg_time = start_time
	while bkg_time <= config['custom']['end_time']:
		bkg_times.append(bkg_time)
		bkg_time = bkg_time.add(seconds=interval_seconds)
	if len(bkg_times) == 0: cli.error('Failed to set background times, check start_time and forecast_hours.')

	expected_files = [f'FILE:{time.format("YYYY-MM-DD_HH")}' for time in bkg_times]
	if not check_files(expected_files) or args.force:
		run('rm -f GRIBFILE.* FILE:*')
		if 'background' in config['custom']:
			if not os.path.isdir(f'{wps_work_dir}/background'): os.mkdir(f'{wps_work_dir}/background')
			os.chdir(f'{wps_work_dir}/background')
			for bkg_time in bkg_times:
				try:
					bkg_dir = eval_bkg_dir(bkg_start_time, bkg_time)
					if type(config['custom']['background']['file_pattern']) == list:
						file_patterns = config['custom']['background']['file_pattern']
					else:
						file_patterns = [config['custom']['background']['file_pattern']]
					for file_pattern in file_patterns:
						rendered_file_pattern = Template(file_pattern).render(bkg_start_time=bkg_start_time, bkg_time=bkg_time, bkg_forecast_hour=(bkg_time-bkg_start_time).in_hours())
						bkg_file = glob(bkg_dir + '/' + rendered_file_pattern)[0]
						bkg_file_basename = os.path.basename(bkg_file)
						# Process background file when there is file_processes in config.
						if 'file_processes' in config['custom']['background']:
							for file_process in config['custom']['background']['file_processes']:
								run(Template(file_process).render(
									bkg_file=bkg_file,
									bkg_file_basename=bkg_file_basename,
									bkg_start_time=bkg_start_time,
									bkg_time=bkg_time
								))
						run(f'ln -sf {bkg_file} {bkg_time.format("YYYYMMDDHH")}_{bkg_file_basename}')
				except Exception as e:
					print(e)
					print(bkg_dir + '/' + rendered_file_pattern)
					cli.error(f'Failed to link background file!')
			os.chdir(wps_work_dir)
			run(f'{wps_root}/link_grib.csh {wps_work_dir}/background/*')
		else:
			bkg_dir = eval_bkg_dir(bkg_start_time, bkg_start_time)
			if len(glob(f'{bkg_dir}/*.0p25.*')) > 0:
				res = '0p25'
			elif len(glob(f'{bkg_dir}/*.0p50.*')) > 0:
				res = '0p50'
			elif len(glob(f'{bkg_dir}/*.1p00.*')) > 0:
				res = '1p00'
			else:
				cli.error(f'There is no GFS data in {bkg_dir}!')
			run(f'{wps_root}/link_grib.csh {bkg_dir}/*.{res}.*')
		# When the surface and vertical levels are separated, we can only use 1 process to run ungrib.exe.
		submit_job(f'{wps_root}/ungrib/src/ungrib.exe', 1, config, args, logfile='ungrib.log', wait=True)
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {wps_work_dir}/ungrib.out.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File FILE:* already exist.')
	run('ls -l FILE:*')

	cli.stage(f'Run metgrid.exe at {wps_work_dir} ...')
	copy(f'{wps_root}/metgrid/METGRID.TBL.ARW', 'METGRID.TBL')
	expected_files = ['met_em.d01.{}.nc'.format(time.format('YYYY-MM-DD_HH:mm:ss')) for time in bkg_times]
	if not check_files(expected_files) or args.force:
		# Remove possible existing met_em files.
		run('rm -f met_em.*')
		submit_job(f'{wps_root}/metgrid/src/metgrid.exe', args.np, config, args, logfile='metgrid.log.0000', wait=True)
		if not check_files(expected_files):
			cli.error(f'Failed! Check output {wps_work_dir}/metgrid.log.0000.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File met_em.* already exist.')
	run('ls -l met_em.*')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WPS system.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-b', '--bkg-root', dest='bkg_root', help='Background root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
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

	if not args.bkg_root:
		if os.getenv('BKG_ROOT'):
			args.bkg_root = os.getenv('BKG_ROOT')
		else:
			cli.error('Option --bkg-root or environment variable BKG_ROOT need to be set!')
	args.bkg_root = os.path.abspath(args.bkg_root)
	if not os.path.isdir(args.bkg_root):
		cli.error(f'Directory {args.bkg_root} does not exist!')
	
	config = parse_config(args.config_json)

	run_wps_ungrib_metgrid(args.work_root, args.wps_root, args.bkg_root, config, args)
