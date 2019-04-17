#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
from jinja2 import Template
import re
from shutil import copy
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wps_ungrib_metgrid(work_root, wps_root, bkg_root, config, args):
	if 'background' in config['custom'] and 'type' in config['custom']['background']:
		bkg_type = config['custom']['background']['type']
	else:
		bkg_type = 'gfs'

	wps_work_dir = os.path.abspath(work_root) + '/wps'
	if not os.path.isdir(wps_work_dir):
		cli.error(f'Directory {wps_work_dir} does not exist! Run GEOGRID first.')
	os.chdir(wps_work_dir)

	cli.stage(f'Run ungrib.exe at {wps_work_dir} ...')
	if 'background' in config['custom'] and 'vtable' in config['custom']['background']:
		run(f'ln -sf {config["custom"]["background"]["vtable"]} {wps_work_dir}/Vtable')
	else:
		run(f'ln -sf {wps_root}/ungrib/Variable_Tables/Vtable.{bkg_type.upper()} {wps_work_dir}/Vtable')

	def eval_bkg_dir(bkg_start_time):
		if 'background' in config['custom'] and 'dir_pattern' in config['custom']['background']:
			return bkg_root + '/' + Template(config['custom']['background']['dir_pattern']).render(bkg_start_time=bkg_start_time)
		elif bkg_type == 'gfs':
			return bkg_root + '/gfs.' + bkg_start_time.format('YYYYMMDDHH')

	# Find out suitable background data that cover forecast time period.
	def is_bkg_exist(bkg_start_time):
		bkg_dir = eval_bkg_dir(bkg_start_time)
		if 'background' in config['custom'] and 'file_pattern' in config['custom']['background']:
			file_name = Template(config['custom']['background']['file_pattern']).render(bkg_start_time=bkg_start_time)
		elif bkg_type == 'gfs':
			file_name = 'gfs.t{:02d}z.pgrb2.*.f*'.format(bkg_start_time.hour)
		return len(glob(f'{bkg_dir}/{file_name}')) != 0

	found = False
	for date in (config['custom']['start_time'], config['custom']['start_time'].subtract(days=1)):
		if found: break
		for hour in (18, 12, 6, 0):
			bkg_start_time = pendulum.datetime(date.year, date.month, date.day, hour)
			if ((config['custom']['start_time'] - date).days == 1 or config['custom']['start_time'].hour >= hour) and is_bkg_exist(bkg_start_time):
				found = True
				break
	if not found: cli.error('Background data is not available!')
	cli.notice(f'Use background starting from {bkg_start_time}.')

	# Generate the background times.
	interval_seconds = int(re.search('interval_seconds\s*=\s*(\d+)', open('./namelist.wps').read())[1])
	bkg_times = []
	bkg_time = bkg_start_time
	while bkg_time <= config['custom']['end_time']:
		if bkg_time >= config['custom']['start_time']:
			bkg_times.append(bkg_time)
		bkg_time = bkg_time.add(seconds=interval_seconds)
	if len(bkg_times) == 0: cli.error('Failed to set background times, check start_time and forecast_hours.')

	bkg_dir = eval_bkg_dir(bkg_start_time)
	expected_files = [f'FILE:{time.format("YYYY-MM-DD_HH")}' for time in bkg_times]
	if not check_files(expected_files) or args.force:
		run('rm -f GRIBFILE.* FILE:*')
		if 'background' in config['custom'] and 'file_processes' in config['custom']['background']:
			if not os.path.isdir(f'{wps_work_dir}/background'): os.mkdir(f'{wps_work_dir}/background')
			os.chdir(f'{wps_work_dir}/background')
			for bkg_time in bkg_times:
				try:
					bkg_file = glob(bkg_dir + '/' + Template(config['custom']['background']['file_pattern']).render(bkg_start_time=bkg_start_time, bkg_time=bkg_time))[0]
					for file_process in config['custom']['background']['file_processes']:
						run(Template(file_process).render(bkg_file=bkg_file, bkg_file_basename=os.path.basename(bkg_file), bkg_start_time=bkg_start_time, bkg_time=bkg_time))
				except:
					continue
			os.chdir(wps_work_dir)
			run(f'{wps_root}/link_grib.csh {wps_work_dir}/background/*')
		else:
			if len(glob(f'{bkg_dir}/*.0p25.*')) > 0:
				res = '0p25'
			elif len(glob(f'{bkg_dir}/*.0p50.*')) > 0:
				res = '0p50'
			elif len(glob(f'{bkg_dir}/*.1p00.*')) > 0:
				res = '1p00'
			else:
				cli.error(f'There is no GFS data in {bkg_dir}!')
			run(f'{wps_root}/link_grib.csh {bkg_dir}/*.{res}.*')
		if args.verbose:
			run(f'{wps_root}/ungrib/src/ungrib.exe')
		else:
			run(f'{wps_root}/ungrib/src/ungrib.exe &> ungrib.out')
		if not check_files(expected_files):
			if args.verbose:
				cli.error('Failed!')
			else:
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
		if args.verbose:
			run(f'{wps_root}/metgrid/src/metgrid.exe')
		else:
			run(f'{wps_root}/metgrid/src/metgrid.exe > metgrid.out 2>&1')
		if not check_files(expected_files):
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error('Failed! Check output {}/metgrid.out.'.format(wps_root))
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
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
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
