#!/usr/bin/env python3

import argparse
import copy
from netCDF4 import Dataset
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, parse_config, run, copy_netcdf_file, wrf_version, Version
import wrf_operators as wrf

parser = argparse.ArgumentParser(description="Run WRF FSO.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
parser.add_argument(      '--wps-root', dest='wps_root', help='WPS root directory (e.g. WPS)')
parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRFV3 or WRF)')
parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
parser.add_argument(      '--wrfplus-root', dest='wrfplus_root', help='WRFPLUS root directory (e.g. WRFPLUS)')    
parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
parser.add_argument('-g', '--geog-root', dest='geog_root', help='GEOG data root directory (e.g. WPS_GEOG)')
parser.add_argument('-b', '--bkg-root', dest='bkg_root', help='Background root directory')
parser.add_argument('-l', '--littler-root', dest='littler_root', help='LITTLE_R data root directory')
parser.add_argument('-p', '--prepbufr-root', dest='prepbufr_root', help='PrepBUFR data root directory')
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF.', default=2, type=int)
parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs.', action='store_true')
parser.add_argument(      '--pbs', help='Use PBS job management system variants (e.g. TORQUE) to run MPI jobs.', action='store_true')
parser.add_argument('-v', '--verbose', help='Print out work log', action='store_true')
parser.add_argument('-f', '--force', help='Force to run', action='store_true')
args = parser.parse_args()

if not args.work_root:
	if os.getenv('WORK_ROOT'):
		args.work_root = os.getenv('WORK_ROOT')
	else:
		cli.error('Option --work-root or environment variable WORK_ROOT need to be set!')
args.work_root = os.path.abspath(args.work_root)
if not os.path.isdir(args.work_root):
	os.makedirs(args.work_root)
	cli.notice(f'Create work directory {args.work_root}.')

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

if not args.wrfplus_root:
	if os.getenv('WRFPLUS_ROOT'):
		args.wrfplus_root = os.getenv('WRFPLUS_ROOT')
	elif args.codes:
		args.wrfplus_root = args.codes + '/WRFPLUS'
	else:
		cli.error('Option --wrfplus-root or environment variable WRFPLUS_ROOT need to be set!')
args.wrfplus_root = os.path.abspath(args.wrfplus_root)
if not os.path.isdir(args.wrfplus_root):
	cli.error(f'Directory {args.wrfplus_root} does not exist!')

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

version = wrf_version(args.wrf_root)
if version >= Version('4.0'):
	cli.error('WRFPLUS 4.0 does not pass tangient and adjoint tests!')
if not version in (Version('3.6.1'), Version('3.8.1'), Version('3.9.1')):
	cli.error('Only WRF 3.6.1, 3.8.1 and 3.9.1 have been tested for FSO application!')

config = parse_config(args.config_json)

if config['wrfda']['ob_format'] == 1:
	if not args.prepbufr_root:
		if os.getenv('PREPBUFR_ROOT'):
			args.prepbufr_root = os.getenv('PREPBUFR_ROOT')
		else:
			cli.error('Option --prepbufr-root or environment variable PREPBUFR_ROOT need to be set!')
	args.prepbufr_root = os.path.abspath(args.prepbufr_root)
	if not os.path.isdir(args.prepbufr_root):
		cli.error(f'Directory {args.prepbufr_root} does not exist!')
elif config['wrfda']['ob_format'] == 2:
	if not args.littler_root:
		if os.getenv('LITTLER_ROOT'):
			args.littler_root = os.getenv('LITTLER_ROOT')
		else:
			cli.error('Option --littler-root or environment variable LITTLER_ROOT need to be set!')
	args.littler_root = os.path.abspath(args.littler_root)
	if not os.path.isdir(args.littler_root):
		cli.error(f'Directory {args.littler_root} does not exist!')

start_time = config['custom']['start_time']
end_time = config['custom']['end_time']
datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
start_time_str = start_time.format(datetime_fmt)
end_time_str = end_time.format(datetime_fmt)

if not os.path.isdir(args.work_root + '/fb'):  os.mkdir(args.work_root + '/fb')
if not os.path.isdir(args.work_root + '/fa'):  os.mkdir(args.work_root + '/fa')
if not os.path.isdir(args.work_root + '/ref'): os.mkdir(args.work_root + '/ref')

wrf.config_wps(args.work_root, args.wps_root, args.geog_root, config, args)
wrf.run_wps_geogrid(args.work_root, args.wps_root, config, args)

# Spin up 6 hours.
spinup_config = copy.deepcopy(config)
spinup_config['custom']['start_time'] = config['custom']['start_time'].subtract(hours=6)
spinup_config['custom']['forecast_hours'] += 6
wrf.config_wps(args.work_root, args.wps_root, args.geog_root, spinup_config, args)

# Run forecast with xb as initial condition.
cli.banner('                   Run forecast with xb as initial condition')
wrf.run_wps_ungrib_metgrid(args.work_root, args.wps_root, args.bkg_root, spinup_config, args)
wrf.config_wrf(args.work_root + '/fb', args.wrf_root, args.wrfda_root, spinup_config, args)
wrf.run_real(args.work_root + '/fb', args.work_root + '/wps', args.wrf_root, spinup_config, args)
wrf.run_wrf(args.work_root + '/fb', args.wrf_root, spinup_config, args)

# Run forecast with xa as initial condition.
cli.banner('                   Run forecast with xa as initial condition')
if not os.path.isdir(args.work_root + '/fa/wrf'): os.mkdir(args.work_root + '/fa/wrf')
run(f'cp {args.work_root}/fb/wrf/wrfout_d01_{start_time_str} {args.work_root}/fa/wrf/wrfinput_d01_{start_time_str}')
run(f'cp {args.work_root}/fb/wrf/wrfbdy_d01 {args.work_root}/fa/wrf/wrfbdy_d01_{start_time_str}')
wrf.config_wrfda(args.work_root + '/fa', args.wrfda_root, config, args)
if config['wrfda']['ob_format'] == 2:
	wrf.run_wrfda_obsproc(args.work_root + '/fa', args.wrfda_root, args.littler_root, config, args)
wrf.run_wrfda_3dvar(args.work_root + '/fa', args.wrfda_root, config, args)
wrf.run_wrfda_update_bc(args.work_root + '/fa', args.wrfda_root, False, config, args)
wrf.config_wrf(args.work_root + '/fa', args.wrf_root, args.wrfda_root, config, args)
wrf.run_wrf(args.work_root + '/fa', args.wrf_root, config, args)

# Interpolate reference at valid time.
cli.banner('                   Interpolate reference at valid time')
ref_config = copy.deepcopy(config)
ref_config['custom']['start_time'] = config['custom']['end_time']
wrf.config_wps(args.work_root + '/ref', args.wps_root, args.geog_root, ref_config, args)
run(f'ln -sf {args.work_root}/wps/geo_em.d01.nc {args.work_root}/ref/wps')
wrf.run_wps_ungrib_metgrid(args.work_root + '/ref', args.wps_root, args.bkg_root, ref_config, args)
wrf.config_wrf(args.work_root + '/ref', args.wrf_root, args.wrfda_root, ref_config, args)
wrf.run_real(args.work_root + '/ref', args.work_root + '/ref/wps', args.wrf_root, ref_config, args)
 
# Calculate forecast error measures.
cli.banner('                   Calculate forecast error measures')
if not os.path.isdir(args.work_root + '/fa/wrfplus'): os.mkdir(args.work_root + '/fa/wrfplus')
if not os.path.isdir(args.work_root + '/fb/wrfplus'): os.mkdir(args.work_root + '/fb/wrfplus')

xt  = Dataset(f'{args.work_root}/ref/wrf/wrfinput_d01_{end_time_str}', 'r')
xaf = Dataset(f'{args.work_root}/fa/wrf/wrfout_d01_{end_time_str}',    'r')
xbf = Dataset(f'{args.work_root}/fb/wrf/wrfout_d01_{end_time_str}',    'r')

def calc_final_sens(a, b, c):
	for var_name in ('U', 'V', 'T', 'P'):
		xa = a.variables[var_name]
		xb = b.variables[var_name]
		if not f'A_{var_name}' in c.variables: c.createVariable(f'A_{var_name}', xa.datatype, xa.dimensions)
		xc = c.variables[f'A_{var_name}']
		xc.setncatts(xa.__dict__)
		xc[:] = 0.0
		xc[:] = xa[:] - xb[:]
		if var_name == 'T':
			xc[:] = xc[:] * (9.8 / 3)**2
		elif var_name == 'P':
			xc[:] = xc[:] * (1.0 / 300.0)**2

if not os.path.isfile(f'{args.work_root}/fa/wrfplus/final_sens_d01') or args.force:
	cli.notice(f'Calculate final sensitivity {args.work_root}/fa/wrfplus/final_sens_d01.')
	run(f'cp {args.work_root}/fa/wrf/wrfout_d01_{end_time_str} {args.work_root}/fa/wrfplus/final_sens_d01')
	saf = Dataset(f'{args.work_root}/fa/wrfplus/final_sens_d01', 'r+')
	calc_final_sens(xaf, xt, saf)
	saf.close()
else:
	run(f'ls -l {args.work_root}/fa/wrfplus/final_sens_d01')

if not os.path.isfile(f'{args.work_root}/fb/wrfplus/final_sens_d01'):
	cli.notice(f'Calculate final sensitivity {args.work_root}/fb/wrfplus/final_sens_d01.')
	run(f'cp {args.work_root}/fb/wrf/wrfout_d01_{end_time_str} {args.work_root}/fb/wrfplus/final_sens_d01')
	sbf = Dataset(f'{args.work_root}/fb/wrfplus/final_sens_d01', 'r+')
	calc_final_sens(xbf, xt, sbf)
	sbf.close()
else:
	run(f'ls -l {args.work_root}/fb/wrfplus/final_sens_d01')

# Run adjoint model with forecast error.
cli.banner('                   Run adjoint for forecast from background')
wrf.config_wrfplus(args.work_root + '/fb', args.wrfplus_root, config, args)
wrf.run_wrfplus_ad(args.work_root + '/fb', args.wrfplus_root, config, args)
wrf.config_wrfplus(args.work_root + '/fa', args.wrfplus_root, config, args)
wrf.run_wrfplus_ad(args.work_root + '/fa', args.wrfplus_root, config, args)

# Calculate forecast sensitivity.
cli.banner('                   Calculate forecast sensitivity')

if not os.path.isdir(f'{args.work_root}/sens'): os.mkdir(args.work_root + '/sens')

wrf.config_wrfda_sens(args.work_root + '/sens', args.wrfda_root, config, args, args.work_root + '/fa/wrf')

cli.notice('Add two init_sens_d01 data.')
os.chdir(args.work_root + '/sens/wrfda')

def add_init_sens(a, b, c):
	for var_name in ('A_U', 'A_V', 'A_T', 'A_W', 'A_PH', 'A_MU', 'A_QVAPOR'):
		xa = a.variables[var_name]
		xb = b.variables[var_name]
		xc = c.variables[var_name]
		xc[:] = xa[:] + xb[:]

run(f'cp {args.work_root}/fa/wrfplus/init_sens_d01_{start_time_str} ad_d01_{start_time_str}')
sa = Dataset(f'{args.work_root}/fa/wrfplus/init_sens_d01_{start_time_str}', 'r')
sb = Dataset(f'{args.work_root}/fb/wrfplus/init_sens_d01_{start_time_str}', 'r')
ad = Dataset(f'ad_d01_{start_time_str}', 'r+')
add_init_sens(sa, sb, ad)
sa.close()
sb.close()
ad.close()
run(f'ln -sf ad_d01_{start_time_str} gr01')
if config['wrfda']['ob_format'] == 2:
	if not os.path.isdir('obsproc'): os.makedirs('obsproc')
	run(f'ln -sf {args.work_root}/fa/wrfda/obsproc/obs_gts_{start_time_str}.3DVAR obsproc')
run(f'ln -sf {args.work_root}/fa/lanczos_eigenpairs.* ..')

wrf.run_wrfda_3dvar(args.work_root + '/sens', args.wrfda_root, config, args, args.work_root + '/fa/wrf')
