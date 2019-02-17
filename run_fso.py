#!/usr/bin/env python3

import argparse
import copy
from netCDF4 import Dataset
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, parse_config, run
import wrf_operators as wrf

parser = argparse.ArgumentParser(description="Run WRF FSO.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
parser.add_argument(      '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3)')
parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WPS)')    
parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
parser.add_argument('-p', '--prod-root', dest='prod_root', help='Product root directory')
parser.add_argument('-g', '--geog-root', dest='geog_root', help='GEOG data root directory (e.g. WPS_GEOG)')
parser.add_argument('-b', '--bkg-root', dest='bkg_root', help='Background root directory')
parser.add_argument('-l', '--littler-root', dest='littler_root', help='Little_r data root directory')
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
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

if not args.prod_root:
	if os.getenv('PROD_ROOT'):
		args.prod_root = os.getenv('PROD_ROOT')
	else:
		cli.error('Option --prod-root or environment variable PROD_ROOT need to be set!')
args.prod_root = os.path.abspath(args.prod_root)
if not os.path.isdir(args.prod_root):
	cli.error(f'Directory {args.prod_root} does not exist!')

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

if not args.geog_root:
	if os.getenv('WPS_GEOG_ROOT'):
		args.geog_root = os.getenv('WPS_GEOG_ROOT')
	elif args.codes:
		args.geog_root = args.codes + '/WPS_GEOG'
	else:
		cli.error('Option --geog-root or environment variable WPS_GEOG_ROOT need to be set!')
args.geog_root = os.path.abspath(args.geog_root)
if not os.path.isdir(args.geog_root):
	cli.error(f'Directory {args.geog_root} does not exist!')

if not args.bkg_root:
	if os.getenv('BKG_ROOT'):
		args.bkg_root = os.getenv('BKG_ROOT')
	else:
		cli.error('Option --bkg-root or environment variable BKG_ROOT need to be set!')
args.bkg_root = os.path.abspath(args.bkg_root)
if not os.path.isdir(args.bkg_root):
	cli.error(f'Directory {args.bkg_root} does not exist!')

if not args.littler_root:
	if os.getenv('LITTLER_ROOT'):
		args.littler_root = os.getenv('LITTLER_ROOT')
	else:
		cli.error('Option --littler-root or environment variable LITTLER_ROOT need to be set!')
args.littler_root = os.path.abspath(args.littler_root)
if not os.path.isdir(args.littler_root):
	cli.error(f'Directory {args.littler_root} does not exist!')

config = parse_config(args.config_json)

start_time = config['common']['start_time']
end_time = config['common']['end_time']
datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
start_time_str = start_time.format(datetime_fmt)
end_time_str = end_time.format(datetime_fmt)

if not os.path.isdir(args.work_root + '/fb'):
	os.mkdir(args.work_root + '/fb')
if not os.path.isdir(args.work_root + '/fa'):
	os.mkdir(args.work_root + '/fa')
if not os.path.isdir(args.work_root + '/ref'):
	os.mkdir(args.work_root + '/ref')

# Run forecast with xb as initial condition.
wrf.config_wps(args.work_root, args.wps_root, args.geog_root, config, args)
wrf.run_wps(args.work_root, args.wps_root, args.bkg_root, config, args)
wrf.config_wrf(args.work_root + '/fb', args.wrf_root, args.wrfda_root, config, args)
wrf.run_real(args.work_root + '/fb', args.work_root + '/wps', args.wrf_root, config, args)
wrf.run_wrf(args.work_root + '/fb', args.wrf_root, config, args)

# Run forecast with xa as initial condition.
wrf.config_wrfda(args.work_root + '/fa', args.wrfda_root, config, args)
wrf.run_wrfda_obsproc(args.work_root + '/fa', args.wrfda_root, args.littler_root, config, args)
if not os.path.isdir(args.work_root + '/fa/wrf'):
	os.mkdir(args.work_root + '/fa/wrf')
run(f'cp {args.work_root}/fb/wrf/wrfinput_d*_{start_time_str} {args.work_root}/fa/wrf')
run(f'cp {args.work_root}/fb/wrf/wrfbdy_d01_{start_time_str} {args.work_root}/fa/wrf')
wrf.run_wrfda_3dvar(args.work_root + '/fa', args.wrfda_root, config, args)
wrf.run_wrfda_update_bc(args.work_root + '/fa', args.wrfda_root, False, config, args)
wrf.config_wrf(args.work_root + '/fa', args.wrf_root, args.wrfda_root, config, args)
wrf.run_wrf(args.work_root + '/fa', args.wrf_root, config, args)

# Interpolate reference at valid time.
ref_config = copy.deepcopy(config)
ref_config['common']['start_time'] = config['common']['end_time']
wrf.config_wps(args.work_root + '/ref', args.wps_root, args.geog_root, ref_config, args)
wrf.run_wps(args.work_root + '/ref', args.wps_root, args.bkg_root, ref_config, args)
wrf.config_wrf(args.work_root + '/ref', args.wrf_root, args.wrfda_root, ref_config, args)
wrf.run_real(args.work_root + '/ref', args.work_root + '/ref/wps', args.wrf_root, ref_config, args)
 
# Calculate forecast error measures.
fa  = Dataset(f'{args.work_root}/fa/wrf/wrfout_d01_{start_time_str}', 'r+')
fb  = Dataset(f'{args.work_root}/fb/wrf/wrfout_d01_{start_time_str}', 'r+')
ref = Dataset(f'{args.work_root}/ref/wrf/wrfinput_d01_{end_time_str}', 'r')

for var_name in ('U', 'V', 'T', 'P'):
	var_fa = fa.variables[var_name]
	var_fb = fb.variables[var_name]
	var_ref = ref.variables[var_name]
	if not f'A_{var_name}' in fa.variables: fa.createVariable(f'A_{var_name}', var_fa.dtype, var_fa.dimensions)
	if not f'A_{var_name}' in fb.variables: fb.createVariable(f'A_{var_name}', var_fb.dtype, var_fb.dimensions)
	var_fa_ref = fa.variables[f'A_{var_name}']
	var_fa_ref[:] = 0.0
	var_fa_ref[:] = var_fa[:] - var_ref[:]
	var_fb_ref = fb.variables[f'A_{var_name}']
	var_fb_ref[:] = 0.0
	var_fb_ref[:] = var_fb[:] - var_ref[:]
	if var_name == 'T':
		var_fa_ref[:] = var_fa_ref[:] * (9.8 / 3)**2
		var_fb_ref[:] = var_fb_ref[:] * (9.8 / 3)**2
	elif var_name == 'P':
		var_fa_ref[:] = var_fa_ref[:] * (1.0 / 300.0)**2
		var_fb_ref[:] = var_fb_ref[:] * (1.0 / 300.0)**2

# Run adjoint with 
