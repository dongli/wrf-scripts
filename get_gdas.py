#!/usr/bin/env python3

root_url = 'https://ftp.ncep.noaa.gov/data/nccf/com/gfs/prod'

import subprocess
import argparse
import pendulum
import re
import requests
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import parse_time, parse_forecast_hours, edit_file, run, cli, check_files, check_file_size, is_downloading

def get_gdas(output_root, start_time, end_time, args):
	if not os.path.isdir(output_root):
		os.makedirs(output_root)
		cli.notice(f'Create directory {output_root}.')

	def download_gdas(time):
		dir_name = f'gdas.{time.format("YYYYMMDD")}/{time.format("HH")}'
		res = requests.head(f'{root_url}/{dir_name}/')
		if res.status_code != 200 and res.status_code != 302:
			cli.error(f'Remote GDAS data at {time} do not exist!')
		file_name = 'gdas.t{:02d}z.prepbufr.nr'.format(time.hour)
		url = f'{root_url}/{dir_name}/{file_name}'
		if not os.path.isdir(f'{output_root}/{dir_name}'):
			os.makedirs(f'{output_root}/{dir_name}')
			cli.notice(f'Create directory {output_root}/{dir_name}.')
		cli.notice(f'Downloading {url}.')
		local_file_path = f'{output_root}/{dir_name}/{file_name}'
		if is_downloading(local_file_path):
			cli.warning(f'Skip downloading {local_file_path}.')
			return
		if os.path.isfile(local_file_path):
			if check_file_size(url, local_file_path):
				cli.notice(f'File {local_file_path} exists.')
				return
			else:
				# File is not downloaded completely.
				os.remove(local_file_path)
		try:
			subprocess.call(['curl', '-C', '-', '-o', local_file_path, url])
		except Exception as e:
			cli.error(f'Encounter exception {e}!')
		if not check_file_size(url, local_file_path):
			os.remove(local_file_path)
			cli.error(f'Failed to download {file_name}!')

	for time in pendulum.period(start_time, end_time).range('hours', 6):
		download_gdas(time)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Get GDAS observation data.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-o', '--output-root', dest='output_root', default='.', help='Root directory to store GDAS data.')
	parser.add_argument('-s', '--start-time', dest='start_time', help='Download GDAS data start in this date time (YYYYMMDDHH).', type=parse_time)
	parser.add_argument('-e', '--end-time', dest='end_time', help='Download GDAS data end in this date time (YYYYMMDDHH).', type=parse_time)
	args = parser.parse_args()
	
	if not args.output_root:
		if os.getenv('RAWDATA_ROOT'):
			args.output_root = os.getenv('RAWDATA_ROOT') + '/gfs'
		else:
			cli.error('Option --output-root or environment variable RAWDATA_ROOT need to be set!')
	args.output_root = os.path.abspath(args.output_root)
	if not os.path.isdir(args.output_root):
		cli.error(f'Directory {args.output_root} does not exist!')

	if not args.end_time:
		args.end_time = args.start_time

	get_gdas(args.output_root, args.start_time, args.end_time, args)
