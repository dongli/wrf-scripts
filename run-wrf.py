#!/usr/bin/env python3.6

import argparse
import fileinput
from glob import glob
import netCDF4
import os
import pendulum
import re
from shutil import copyfile

def parse_time(string):
	match = re.match(r'(\d{4}\d{2}\d{2}\d{2})(\d{2})?', string)
	if match.group(2):
		return pendulum.from_format(string, '%Y%m%d%H%M')
	else:
		return pendulum.from_format(string, '%Y%m%d%H')

parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-t', '--template-root', dest='template_root', help='Configuration directory containing namelist.wps and other files')
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRFV3, WPS)')
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
parser.add_argument('-p', '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument('-g', '--gfs-root', dest='gfs_root', help='GFS root directory (e.g. gfs)')
parser.add_argument('-s', '--start-date', dest='start_date', help='Start date time (e.g. YYYYmmddHH)', type=parse_time)
parser.add_argument('-f', '--forecast-hours', dest='forecast_hours', help='Forecast hours (e.g. 48)', type=int)
parser.add_argument('-r', '--resolution', help='Coarsest grid resolution in kilometer.', type=float)
parser.add_argument('--force', help='Force to run', action='store_true')
args = parser.parse_args()

script_root = os.path.dirname(os.path.realpath(__file__))

if not args.template_root:
	if os.getenv('TEMPLATE_ROOT'):
		args.template_root = os.getenv('TEMPLATE_ROOT')
	elif os.path.isdir('{}/config'.format(script_root)):
		args.template_root = '{}/config'.format(script_root)
	else:
		print('[Error]: Option --config-root or environment variable TEMPLATE_ROOT need to be set!')
		exit(1)

args.template_root = os.path.abspath(args.template_root)

if not args.wrf_root:
	if os.getenv('WRF_ROOT'):
		args.wrf_root = os.getenv('WRF_ROOT')
	elif args.codes:
		args.wrf_root = args.codes + '/WRFV3'
	else:
		print('[Error]: Option --wrf-root or environment variable WRF_ROOT need to be set!')
		exit(1)

if not args.wps_root:
	if os.getenv('WPS_ROOT'):
		args.wps_root = os.getenv('WPS_ROOT')
	elif args.codes:
		args.wps_root = args.codes + '/WPS'
	else:
		print('[Error]: Option --wps-root or environment variable WPS_ROOT need to be set!')
		exit(1)

if not args.gfs_root:
	if os.getenv('GFS_ROOT'):
		args.gfs_root = os.getenv('GFS_ROOT')
	else:
		print('[Error]: Option --gfs-root or environment variable GFS_ROOT need to be set!')
		exit(1)

def edit_file(filepath, changes):
	try:
		with fileinput.FileInput(filepath, inplace=True) as file:
			for line in file:
				found = False
				for change in changes:
					if re.search(change[0], line, re.I):
						print(change[1])
						found = True
						break
				if not found:
					print(line, end='')
	except Exception as e:
		print('[Error]: Failed to edit file {}! {}'.format(filepath, e))
		exit(1)

def check_files(expected_files):
	result = True
	for file in expected_files:
		if not os.path.isfile(file):
			result = False
			break
	return result

end_date = args.start_date.add(hours=args.forecast_hours)
datetime_fmt = '%Y-%m-%d_%H:%M:%S'

# ------------------------------------------------------------------------------
#                                    WPS

os.chdir(args.wps_root)

copyfile(args.template_root + '/namelist.wps', './namelist.wps')
max_dom = int(re.search('max_dom\s*=\s*(\d+)', open('./namelist.wps').read())[1])

# Set start and end dates in namelist.wps.
if max_dom > 3:
	print('[Error]: Sorry, we just add support for 3 max_dom. You may need to edit script.')
	exit(0)
edit_file('./namelist.wps', [
	['^\s*start_date.*$', ' start_date = \'{0}\', \'{0}\', \'{0}\''.format(args.start_date.format(datetime_fmt))],
	['^\s*end_date.*$', ' end_date = \'{0}\', \'{1}\', \'{1}\''.format(end_date.format(datetime_fmt), args.start_date.format(datetime_fmt))]
])

print('[Notice]: Run geogrid.exe ...')
if not check_files(['geo_em.d{:02d}.nc'.format(i + 1) for i in range(max_dom)]) or args.force:
	os.system('rm -f geo_em.d*.nc')
	os.system('./geogrid.exe > geogrid.out 2>&1')
	if not check_files(['geo_em.d{:02d}.nc'.format(i + 1) for i in range(max_dom)]):
		print('[Error]: Failed to run geogrid.exe! Check output {}/geogrid.out.'.format(os.path.abspath(args.wps_root)))
		exit(1)
else:
	print('[Notice]: File geo_em.*.nc already exist.')
os.system('ls -l geo_em.*.nc')

print('[Notice]: Run ungrib.exe ...')
# Find out suitable GFS data that cover forecast time period.
def is_gfs_exist(date, hour):
	dir_name = '{}/gfs.{}'.format(args.gfs_root, date.format('%Y%m%d%H'))
	file_name = 'gfs.t{:02d}z.pgrb2.0p25.f{:03d}'.format(date.hour, hour)
	return os.path.isfile('{}/{}'.format(dir_name, file_name))

found = False
for date in (args.start_date, args.start_date.subtract(days=1)):
	if found: break
	for hour in (18, 12, 6, 0):
		if ((args.start_date - date).days == 1 or args.start_date.hour >= hour) and is_gfs_exist(date, hour):
			gfs_start_date = pendulum.create(date.year, date.month, date.day, hour)
			found = True
			break
if not found:
	print('[Error]: GFS data is not available!')
	exit(1)

interval_seconds = int(re.search('interval_seconds\s*=\s*(\d+)', open('./namelist.wps').read())[1])
os.system('ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable')
dt = pendulum.interval(seconds=interval_seconds)
gfs_dates = [gfs_start_date]
while gfs_dates[len(gfs_dates) - 1] < end_date:
	gfs_dates.append(gfs_dates[len(gfs_dates) - 1] + dt)
if not check_files(['FILE:{}'.format(date.format('%Y-%m-%d_%H')) for date in gfs_dates]) or args.force:
	os.system('rm -f FILE:*')
	os.system('./link_grib.csh {}/gfs.{}/*'.format(args.gfs_root, gfs_start_date.format('%Y%m%d%H')))
	os.system('./ungrib.exe > ungrib.out 2>&1')
	if not check_files(['FILE:{}'.format(date.format('%Y-%m-%d_%H')) for date in gfs_dates]):
		print('[Error]: Failed to run ungrib.exe! Check output {}/ungrib.out.'.format(args.wps_root))
		exit(1)
else:
	print('[Noitce]: File FILE:* already exist.')
os.system('ls -l FILE:*')

print('[Notice]: Run metgrid.exe ...')
if not check_files(['met_em.d01.{}.nc'.format(date.format(datetime_fmt)) for date in gfs_dates]) or args.force:
	os.system('./metgrid.exe > metgrid.out 2>&1')
	if not check_files(['met_em.d01.{}.nc'.format(date.format(datetime_fmt)) for date in gfs_dates]):
		print('[Error]: Failed to run metgrid.exe! Check output {}/metgrid.out.'.format(args.wps_root))
		exit(1)
else:
	print('[Notice]: File met_em.* already exist.')
os.system('ls -l met_em.*')

# Collect parameters for WRF.
dataset = netCDF4.Dataset('met_em.d01.{}.nc'.format(gfs_start_date.format(datetime_fmt)), 'r')
num_metgrid_levels = dataset.dimensions['num_metgrid_levels'].size
namelist_wps = open('{}/namelist.wps'.format(args.wps_root)).read()
e_we = [int(x.replace(',', '')) for x in re.search('e_we\s*=\s*(.*)', namelist_wps)[1].split()]
e_sn = [int(x.replace(',', '')) for x in re.search('e_sn\s*=\s*(.*)', namelist_wps)[1].split()]
i_parent_start = [int(x.replace(',', '')) for x in re.search('i_parent_start\s*=\s*(.*)', namelist_wps)[1].split()]
j_parent_start = [int(x.replace(',', '')) for x in re.search('j_parent_start\s*=\s*(.*)', namelist_wps)[1].split()]
parent_grid_ratio = [int(x.replace(',', '')) for x in re.search('parent_grid_ratio\s*=\s*(.*)', namelist_wps)[1].split()]

e_vert = [30, 30, 30]

# ------------------------------------------------------------------------------
#                                    WRF

os.chdir(args.wrf_root + '/run')

copyfile(args.template_root + '/namelist.input', './namelist.input')

edit_file('./namelist.input', [
	['^\s*run_hours.*$', ' run_hours = {},'.format(args.forecast_hours)],
	['^\s*start_year.*$', ' start_year = {0}, {0}, {0},'.format(args.start_date.year)],
	['^\s*start_month.*$', ' start_month = {0}, {0}, {0},'.format(args.start_date.month)],
	['^\s*start_day.*$', ' start_day = {0}, {0}, {0},'.format(args.start_date.day)],
	['^\s*start_hour.*$', ' start_hour = {0}, {0}, {0},'.format(args.start_date.hour)],
	['^\s*end_year.*$', ' end_year = {0}, {0}, {0},'.format(end_date.year)],
	['^\s*end_month.*$', ' end_month = {0}, {0}, {0},'.format(end_date.month)],
	['^\s*end_day.*$', ' end_day = {0}, {0}, {0},'.format(end_date.day)],
	['^\s*end_hour.*$', ' end_hour = {0}, {0}, {0},'.format(end_date.hour)],
	['^\s*num_metgrid_levels.*$', ' num_metgrid_levels = {},'.format(num_metgrid_levels)],
])

if max_dom == 2:
	edit_file('./namelist.input', [
		['^\s*i_parent_start.*$', ' i_parent_start = 1, {}'.format(i_parent_start[1])],
		['^\s*j_parent_start.*$', ' j_parent_start = 1, {}'.format(j_parent_start[1])],
		['^\s*e_we.*$', ' e_we = {}, {},'.format(e_we[0], e_we[1])],
		['^\s*e_sn.*$', ' e_sn = {}, {},'.format(e_sn[0], e_sn[1])],
		['^\s*e_vert.*$', ' e_vert = {}, {},'.format(e_vert[0], e_vert[1])],
		['^\s*dx.*$', ' dx = {}, {}'.format(args.resolution * 1000, args.resolution / parent_grid_ratio[1] * 1000)],
		['^\s*dy.*$', ' dy = {}, {}'.format(args.resolution * 1000, args.resolution / parent_grid_ratio[1] * 1000)],
	])
elif max_dom == 3:
	edit_file('./namelist.input', [
		['^\s*i_parent_start.*$', ' i_parent_start = 1, {}, {},'.format(i_parent_start[1], i_parent_start[2])],
		['^\s*j_parent_start.*$', ' j_parent_start = 1, {}, {},'.format(j_parent_start[1], j_parent_start[2])],
		['^\s*e_we.*$', ' e_we = {}, {}, {},'.format(e_we[0], e_we[1], e_we[2])],
		['^\s*e_sn.*$', ' e_sn = {}, {}, {},'.format(e_sn[0], e_sn[1], e_sn[2])],
		['^\s*e_vert.*$', ' e_vert = {}, {}, {},'.format(e_vert[0], e_vert[1], e_vert[2])],
		['^\s*dx.*$', ' dx = {}, {}, {},'.format(args.resolution * 1000, args.resolution / parent_grid_ratio[1] * 1000, args.resolution / parent_grid_ratio[1] / parent_grid_ratio[2] * 1000)],
		['^\s*dy.*$', ' dy = {}, {}, {},'.format(args.resolution * 1000, args.resolution / parent_grid_ratio[1] * 1000, args.resolution / parent_grid_ratio[1] / parent_grid_ratio[2] * 1000)],
	])

print('[Notice]: Run real.exe ...')
if not check_files(['wrfinput_d{:02d}'.format(i + 1) for i in range(max_dom)] + ['wrfbdy_d01']) or args.force:
	os.system('rm -f wrfinput_*')
	os.system('./real.exe > real.out 2>&1')
	if not check_files(['wrfinput_d{:02d}'.format(i + 1) for i in range(max_dom)] + ['wrfbdy_d01']):
		print('[Error]: Failed to run real.exe! Check output {}/run/real.out.'.format(os.path.abspath(args.wrf_root)))
		exit(1)
else:
	print('[Notice]: File wrfbdy_d01 and wrfinput_* already exist.')
os.system('ls -l wrfbdy_d01 wrfinput_*')

