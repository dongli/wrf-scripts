#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import re
from shutil import copyfile
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, check_files, run, parse_config

def run_wps(wps_root, gfs_root, config, args):
	common_config = config['common']
	
	os.chdir(args.wps_root)
	
	cli.notice('Run geogrid.exe ...')
	expected_files = ['geo_em.d{:02d}.nc'.format(i + 1) for i in range(common_config['max_dom'])]
	if not check_files(expected_files) or args.force:
		run('rm -f geo_em.d*.nc')
		if args.verbose:
			run('./geogrid.exe')
		else:
			run('./geogrid.exe &> geogrid.out')
		if not check_files(expected_files):
			if args.verbose:
				cli.error(f'Failed!')
			else:
				cli.error(f'Failed! Check output {os.path.abspath(wps_root)}/geogrid.out.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File geo_em.*.nc already exist.')
	run(f'ls -l {wps_root}/geo_em.*.nc')
	
	cli.notice('Run ungrib.exe ...')
	# Find out suitable GFS data that cover forecast time period.
	def is_gfs_exist(date, hour):
		dir_name = f'{gfs_root}/gfs.{date.format("YYYYMMDDHH")}'
		file_name = 'gfs.t{:02d}z.pgrb2.0p25.f{:03d}'.format(date.hour, hour)
		return os.path.isfile(f'{dir_name}/{file_name}')
	
	found = False
	for date in (common_config['start_time'], common_config['start_time'].subtract(days=1)):
		if found: break
		for hour in (18, 12, 6, 0):
			if ((common_config['start_time'] - date).days == 1 or common_config['start_time'].hour >= hour) and is_gfs_exist(date, hour):
				gfs_start_date = pendulum.datetime(date.year, date.month, date.day, hour)
				found = True
				break
	if not found:
		cli.error('GFS data is not available!')
	
	interval_seconds = int(re.search('interval_seconds\s*=\s*(\d+)', open('./namelist.wps').read())[1])
	run('ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable')
	gfs_dates = [gfs_start_date]
	while gfs_dates[len(gfs_dates) - 1] < common_config['end_time']:
		gfs_dates.append(gfs_dates[len(gfs_dates) - 1].add(seconds=interval_seconds))
	expected_files = [f'FILE:{date.format("YYYY-MM-DD_HH")}' for date in gfs_dates]
	if not check_files(expected_files) or args.force:
		run('rm -f FILE:*')
		run(f'./link_grib.csh {gfs_root}/gfs.{gfs_start_date.format("YYYYMMDDHH")}/*')
		if args.verbose:
			run('./ungrib.exe')
		else:
			run('./ungrib.exe &> ungrib.out')
		if not check_files(expected_files):
			if args.verbose:
				cli.error('Failed!')
			else:
				cli.error(f'Failed! Check output {wps_root}/ungrib.out.')
		cli.notice('Succeeded.')
	else:
		cli.notice('File FILE:* already exist.')
	run('ls -l FILE:*')
	
	cli.notice('Run metgrid.exe ...')
	expected_files = ['met_em.d01.{}.nc'.format(date.format('YYYY-MM-DD_HH:mm:ss')) for date in gfs_dates]
	if not check_files(expected_files) or args.force:
		# Remove possible existing met_em files.
		run('rm -f met_em.*')
		if args.verbose:
			run('./metgrid.exe')
		else:
			run('./metgrid.exe > metgrid.out 2>&1')
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
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
	parser.add_argument('-b', '--gfs-root', dest='gfs_root', help='GFS root directory (e.g. gfs)')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()
	
	if not args.wps_root:
		if os.getenv('WPS_ROOT'):
			args.wps_root = os.getenv('WPS_ROOT')
		elif args.codes:
			args.wps_root = args.codes + '/WPS'
		else:
			cli.error('Option --wps-root or environment variable WPS_ROOT need to be set!')
	
	args.wps_root = os.path.abspath(args.wps_root)
	
	if not args.gfs_root:
		if os.getenv('GFS_ROOT'):
			args.gfs_root = os.getenv('GFS_ROOT')
		else:
			cli.error('Option --gfs-root or environment variable GFS_ROOT need to be set!')
	
	args.gfs_root = os.path.abspath(args.gfs_root)
	
	config = parse_config(args.config_json)

	run_wps(args.wps_root, args.gfs_root, config, args)
