#!/usr/bin/env python3

import argparse
import ftplib
import math
import pendulum
import re
import os
import pygrib
import shutil
from glob import glob
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, ftp_exist, ftp_list, ftp_get

if not os.getenv('CIMISS_FTP_HOST'):
	cli.error('CIMISS_FTP_HOST is not set!')
if not os.getenv('CIMISS_FTP_USER'):
	cli.error('CIMISS_FTP_USER is not set!')
if not os.getenv('CIMISS_FTP_PASSWD'):
	cli.error('CIMISS_FTP_PASSWD is not set!')

time_interval = pendulum.Duration(hours=6)

def parse_datetime(string):
	match = re.match(r'(\d{4}\d{2}\d{2}\d{2})(\d{2})?', string)
	if match.group(2):
		return pendulum.from_format(string, 'YYYYMMDDHHmm')
	else:
		return pendulum.from_format(string, 'YYYYMMDDHH')

def parse_datetime_range(string):
	match = re.match(r'(\d{4}\d{2}\d{2}\d{2})-(\d{4}\d{2}\d{2}\d{2})', string)
	if not match:
		raise argparse.ArgumentError('"' + string + '" is not a datetime range (YYYYMMDDHH)!')
	return (pendulum.from_format(match.group(1), 'YYYYMMDDHH'), pendulum.from_format(match.group(2), 'YYYYMMDDHH'))

def parse_forecast(string):
	match = re.match(r'(\d+)-(\d+)\+(\d+)', string)
	if match:
		start = int(match.group(1))
		end = int(match.group(2))
		step = int(match.group(3))
		return [x for x in range(start, end + step, step)]
	match = re.findall(r'(\d+):?', string)
	if match:
		return [int(match[i]) for i in range(len(match))]

parser = argparse.ArgumentParser(description='Download GFS data.')
parser.add_argument('-o', '--root-dir', dest='root_dir', help='Root directory to store GFS data.', default='/data/raw/gfs')
parser.add_argument('-t', '--datetime', help='Download data at this datetime (YYYYMMDDHH).', type=parse_datetime)
parser.add_argument('-r', '--datetime-range', dest='datetime_range', help='Download data in this datetime range (YYYYMMDDHH-YYYYMMDDHH).', type=parse_datetime_range)
parser.add_argument('-f', '--forecast', help='Download forecast hours (HH-HH+XX).', type=parse_forecast)
parser.add_argument('-e', '--resolution', help='Set data resolution (1p00, 0p50, 0p25).', default='0p25')
parser.add_argument('-c', '--cycle-period', dest='cycle_period', help='Set LAPS analysis cycle period in seconds.', type=int, default=900)
parser.add_argument('-n', '--cycle-number', dest='cycle_number', help='Set how many cycles that are needed.', type=int, default=6)
args = parser.parse_args()

args.root_dir = os.path.abspath(args.root_dir)
if not os.path.isdir(args.root_dir): os.makedirs(args.root_dir)

if not args.datetime: args.datetime = pendulum.now('UTC')

file_path_pattern = '/NAFP/NCEP/GFS/0p25/{0}/{1:02d}/W_NAFP_C_KWBC_{0}.*0000_P_gfs.t{1:02d}z.pgrb2.0p25.f{2:03d}.bin'

def remote_gfs_exist(date, hour):
	return ftp_exist(ftp, file_path_pattern.format(date.format('YYYYMMDD'), hour, 0), connect)

def download_gfs(datetime, forecast):
	remote_file_path_pattern = file_path_pattern.format(datetime.format('YYYYMMDD'), datetime.hour, forecast)
	remote_dir = os.path.dirname(remote_file_path_pattern)
	local_dir = f'{args.root_dir}/{datetime.format("YYYYMMDDHH")}'
	try:
		remote_file_path = sorted(ftp_list(ftp, remote_file_path_pattern, connect))[-1]
	except IndexError:
		cli.error(f'Failed to get remote_file_path with pattern {remote_file_path_pattern}!')
	ftp_get(ftp, remote_file_path, local_dir, connect, thread_size=40, force=True)

def connect():
	ftp = ftplib.FTP(os.getenv('CIMISS_FTP_HOST'))
	ftp.login(user=os.getenv('CIMISS_FTP_USER'), passwd=os.getenv('CIMISS_FTP_PASSWD'))
	ftp.set_pasv(True)
	return ftp

ftp = connect()

# If datetime is not given, use current system datetime.
# If hour is not a initial hour, and set a suitable hour.
# If remote data is not available, use previous one.
if not args.datetime: args.datetime = pendulum.now('UTC')
analysis_datetime = args.datetime
found = False
for datetime in (args.datetime, args.datetime.subtract(days=1)):
	if found: break
	for hour in (18, 12, 6, 0):
		if ((args.datetime - datetime).days == 1 or args.datetime.hour >= hour) and remote_gfs_exist(datetime, hour):
			args.datetime = pendulum.datetime(datetime.year, datetime.month, datetime.day, hour)
			found = True
			break

if not found:
	cli.error('No valid GFS background is found!')

cli.notice(f'Use forecast cycle {args.datetime}.')

# Set a suitable forecast hours that include analysis hour.
# stmas_mg.exe needs 6 background files.
if not args.forecast:
	dt = analysis_datetime - args.datetime
	# There is no 'tp' variable at the forecast start time, so we need to use the previous forecast cycle.
	if dt.hours <= 5:
		args.datetime -= time_interval
		cli.notice(f'Use forecast cycle {args.datetime} due to dt.hours <= 5.')
		if not remote_gfs_exist(args.datetime, 0):
			cli.error('No valid GFS background is found!')
		dt = analysis_datetime - args.datetime
	args.forecast = []
	for i in range(1 - args.cycle_number, 1):
		if len(args.forecast) == 0:
			hour = int((dt.seconds + i * args.cycle_period) / 3600)
		else:
			hour = math.ceil((dt.seconds + i * args.cycle_period) / 3600)
		if not hour in args.forecast:
			args.forecast.append(hour)

if args.datetime:
	for forecast in args.forecast:
		download_gfs(args.datetime, forecast)
elif args.datetime_range:
	datetime = args.datetime_range[0]
	while datetime <= args.datetime_range[1]:
		for forecast in args.forecast:
			download_gfs(datetime, forecast)
		datetime += time_interval

ftp.quit()
