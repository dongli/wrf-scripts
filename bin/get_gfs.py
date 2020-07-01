#!/usr/bin/env python3

root_url = 'https://www.ftp.ncep.noaa.gov/data/nccf/com/gfs/prod/'

import subprocess
import argparse
import pendulum
import re
import requests
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import parse_time, parse_forecast_hours, edit_file, run, cli, check_files, check_file_size, is_downloading

def get_gfs(output_root, start_time, forecast_hours, resolution, prefix, args):
	if not os.path.isdir(output_root):
		os.makedirs(output_root)
		cli.notice(f'Create directory {output_root}.')

	def download_gfs(start_time, forecast_hour):
		dir_name = f'{prefix}.{start_time.format("YYYYMMDD")}/{start_time.format("HH")}'
		file_name = '{}.t{:02d}z.pgrb2.{}.f{:03d}'.format(prefix, start_time.hour, resolution, forecast_hour)
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
			cli.error('Encounter exception {e}!')
		if not check_file_size(url, local_file_path):
			os.remove(local_file_path)
			cli.error(f'Failed to download {file_name}!')

	res = requests.head(f'{root_url}/{prefix}.{start_time.format("YYYYMMDD")}/{start_time.format("HH")}')
	if res.status_code not in (200, 301):
		print(res.status_code)
		print(f'{root_url}/{prefix}.{start_time.format("YYYYMMDD")}/{start_time.format("HH")}')
		cli.error(f'Remote GFS data at {start_time} do not exist!')

	for forecast_hour in forecast_hours:
		download_gfs(start_time, forecast_hour)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-o', '--output-root', dest='output_root', default='.', help='Root directory to store GFS data.')
	parser.add_argument('-s', '--start-time', dest='start_time', help='Download GFS data start in this date time (YYYYMMDDHH).', type=parse_time)
	parser.add_argument('-f', '--forecast-hours', dest='forecast_hours', help='Download forecast hours (HH-HH+XX).', type=parse_forecast_hours)
	parser.add_argument('-e', '--resolution', help='Set GFS resolution (1p00, 0p50, 0p25).', choices=('1p00', '0p50', '0p25'), default='0p25')
	parser.add_argument('-g', '--gdas', help='Use GDAS analysis.', action='store_true')
	args = parser.parse_args()

	if args.gdas:
		prefix = 'gdas'
	else:
		prefix = 'gfs'

	if not args.output_root:
		if os.getenv('RAWDATA_ROOT'):
			args.output_root = os.getenv('RAWDATA_ROOT') + '/' + prefix
		else:
			cli.error('Option --output-root or environment variable RAWDATA_ROOT need to be set!')
	args.output_root = os.path.abspath(args.output_root)

	get_gfs(args.output_root, args.start_time, args.forecast_hours, args.resolution, prefix, args)
