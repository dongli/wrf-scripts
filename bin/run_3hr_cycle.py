#!/usr/bin/env python3

import argparse
import pendulum
import copy
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../operators')
from utils import cli, parse_time, parse_config, run, copy_netcdf_file, wrf_version, Version
import wrf_operators as wrf

parser = argparse.ArgumentParser(description="Run WRF 3-hour cycle forecast.\n\nNWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
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
parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file')
parser.add_argument('-t', '--start-time', dest='start_time', help='Start forecast time', type=parse_time)
parser.add_argument('-n', '--num-proc', dest='np', help='MPI process number to run WRF', default=2, type=int)
parser.add_argument(      '--ntasks-per-node', dest='ntasks_per_node', help='Override the default setting', default=None, type=int)
parser.add_argument(      '--slurm', help='Use SLURM job management system to run MPI jobs', action='store_true')
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

config = parse_config(args.config_json)
if args.start_time:
	config['custom']['start_time'] = args.start_time
	config['custom']['end_time'] = args.start_time.add(hours=config['custom']['forecast_hours'])

if config['wrfvar3']['ob_format'] == 1:
	if not args.prepbufr_root:
		if os.getenv('PREPBUFR_ROOT'):
			args.prepbufr_root = os.getenv('PREPBUFR_ROOT')
		else:
			cli.error('Option --prepbufr-root or environment variable PREPBUFR_ROOT need to be set!')
	args.prepbufr_root = os.path.abspath(args.prepbufr_root)
	if not os.path.isdir(args.prepbufr_root):
		cli.error(f'Directory {args.prepbufr_root} does not exist!')
elif config['wrfvar3']['ob_format'] == 2:
	if not args.littler_root:
		if os.getenv('LITTLER_ROOT'):
			args.littler_root = os.getenv('LITTLER_ROOT')
		else:
			cli.error('Option --littler-root or environment variable LITTLER_ROOT need to be set!')
	args.littler_root = os.path.abspath(args.littler_root)
	if not os.path.isdir(args.littler_root):
		cli.error(f'Directory {args.littler_root} does not exist!')

wrf.config_wps(args.work_root, args.wps_root, args.geog_root, config, args)
wrf.run_wps_geogrid(args.work_root, args.wps_root, config, args)

start_time = config['custom']['start_time']
end_time = config['custom']['end_time']
datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
start_time_str = start_time.format(datetime_fmt)
end_time_str = end_time.format(datetime_fmt)

# Change work_root to specific date directory.
args.work_root += '/' + start_time.format('YYYYMMDDHH')

def wrfda_conv(config, wrf_work_dir=None, tag=None, fg_d01=None, fg_d02=None, wrfbdy=None):
	# Run conventional data assimilation.
	if not wrf_work_dir: wrf_work_dir = os.path.dirname(fg_d01) if fg_d01 else None
	config['custom']['wrfda']['dom'] = 0
	wrf.config_wrfda(args.work_root, args.wrfda_root, config, args, wrf_work_dir=wrf_work_dir, tag=tag, fg=fg_d01)
	wrf.run_wrfda_obsproc(args.work_root, args.wrfda_root, args.littler_root, config, args, tag=tag)
	wrf.run_wrfda_3dvar(args.work_root, args.wrfda_root, config, args, wrf_work_dir=wrf_work_dir, tag=tag, fg=fg_d01)
	wrf.run_wrfda_update_bc(args.work_root, args.wrfda_root, False, config, args, wrf_work_dir=wrf_work_dir, wrfbdy=wrfbdy, tag=tag)

	if not wrf_work_dir: wrf_work_dir = os.path.dirname(fg_d02) if fg_d02 else None
	config['custom']['wrfda']['dom'] = 1
	wrf.config_wrfda(args.work_root, args.wrfda_root, config, args, wrf_work_dir=wrf_work_dir, tag=tag, fg=fg_d02)
	wrf.run_wrfda_obsproc(args.work_root, args.wrfda_root, args.littler_root, config, args, tag=tag)
	wrf.run_wrfda_3dvar(args.work_root, args.wrfda_root, config, args, wrf_work_dir=wrf_work_dir, tag=tag, fg=fg_d02)

if start_time.hour == 0:
	cli.banner('Run WRF cold run')

	coldrun_config = copy.deepcopy(config)
	coldrun_config['custom']['start_time'] = config['custom']['start_time'].subtract(hours=6)

	# NOTE: Generate more 6hr for next warm run.
	coldrun_config['custom']['forecast_hours'] = 12
	coldrun_config['custom']['end_time'] = coldrun_config['custom']['start_time'].add(hours=coldrun_config['custom']['forecast_hours'])
	wrf.config_wps(args.work_root, args.wps_root, args.geog_root, coldrun_config, args)
	for i in range(coldrun_config['domains']['max_dom']):
		run(f'ln -sf {os.path.dirname(args.work_root)}/wps/geo_em.d{str(i+1).zfill(2)}.nc {args.work_root}/wps/')
	wrf.run_wps_ungrib_metgrid(args.work_root, args.wps_root, args.bkg_root, coldrun_config, args)

	coldrun_config['custom']['end_time'] = coldrun_config['custom']['start_time'].add(hours=coldrun_config['custom']['forecast_hours'])
	wrf.config_wrf(args.work_root, args.wrf_root, args.wrfda_root, coldrun_config, args, tag='coldrun')
	wrf.run_real(args.work_root, args.work_root + '/wps', args.wrf_root, coldrun_config, args, tag='coldrun')

	# Reconfigure WRF for cold run.
	coldrun_config['custom']['forecast_hours'] = 6
	coldrun_config['custom']['end_time'] = coldrun_config['custom']['start_time'].add(hours=coldrun_config['custom']['forecast_hours'])
	wrf.config_wrf(args.work_root, args.wrf_root, args.wrfda_root, coldrun_config, args, tag='coldrun')

	wrfda_conv(coldrun_config, tag='coldrun')

	# Run WRF for 6 hours.
	wrf.run_wrf(args.work_root, args.wrf_root, coldrun_config, args, tag='coldrun')

	fg_d01 = f'{args.work_root}/wrf_coldrun/wrfout_d01_{start_time_str}'
	fg_d02 = f'{args.work_root}/wrf_coldrun/wrfout_d02_{start_time_str}'
	wrfbdy = f'{args.work_root}/wrf_coldrun/wrfbdy_d01'
else:
	wrf.config_wps(args.work_root, args.wps_root, args.geog_root, config, args)
	for i in range(config['domains']['max_dom']):
		run(f'ln -sf {os.path.dirname(args.work_root)}/wps/geo_em.d{str(i+1).zfill(2)}.nc {args.work_root}/wps/')
	wrf.run_wps_ungrib_metgrid(args.work_root, args.wps_root, args.bkg_root, config, args)
	wrf.config_wrf(args.work_root, args.wrf_root, args.wrfda_root, config, args)
	wrf.run_real(args.work_root, args.work_root + '/wps', args.wrf_root, config, args)
	prev_time = start_time.subtract(hours=3)
	prev_work_root = os.path.dirname(args.work_root) + '/' + prev_time.format('YYYYMMDDHH')
	fg_d01 = f'{prev_work_root}/wrf/wrfout_d01_{start_time_str}'
	fg_d02 = f'{prev_work_root}/wrf/wrfout_d02_{start_time_str}'
	wrfbdy = None

wrfda_conv(config, wrf_work_dir=f'{args.work_root}/wrf', fg_d01=fg_d01, fg_d02=fg_d02, wrfbdy=wrfbdy)

# Run radar data assimilation.
cli.banner('Run radar DA')
config['custom']['wrfda']['dom'] = 1
if not 'wrfvar4' in config: config['wrfvar4'] = {}
config['wrfvar1']['write_increments'] = True
config['wrfvar2']['calc_w_increment'] = True
config['wrfvar2']['dt_cloud_model'] = False
config['wrfvar4']['thin_conv'] = True
config['wrfvar4']['thin_rainobs'] = False
config['wrfvar4']['thin_mesh_conv'] = 20
config['wrfvar4']['use_synopobs'] = False
config['wrfvar4']['use_shipsobs'] = False
config['wrfvar4']['use_metarobs'] = False
config['wrfvar4']['use_soundobs'] = False
config['wrfvar4']['use_pilotobs'] = False
config['wrfvar4']['use_airepobs'] = False
config['wrfvar4']['use_satemobs'] = False
config['wrfvar4']['use_geoamvobs'] = False
config['wrfvar4']['use_polaramvobs'] = False
config['wrfvar4']['use_gpsztdobs'] = False
config['wrfvar4']['use_gpspwobs'] = False
config['wrfvar4']['use_gpsrefobs'] = False
config['wrfvar4']['use_profilerobs'] = False
config['wrfvar4']['use_buoyobs'] = False
config['wrfvar4']['use_ssmiretrievalobs'] = False
config['wrfvar4']['use_ssmitbobs'] = False
config['wrfvar4']['use_ssmt1obs'] = False
config['wrfvar4']['use_ssmt2obs'] = False
config['wrfvar4']['use_qscatobs'] = False
config['wrfvar4']['use_bogusobs'] = False
config['wrfvar4']['use_airsretobs'] = False
config['wrfvar4']['use_radarobs'] = True
config['wrfvar4']['use_radar_rv'] = True
config['wrfvar4']['use_radar_rf'] = False
config['wrfvar4']['use_radar_rqv'] = True
config['wrfvar4']['use_radar_rhv'] = True
config['wrfvar4']['use_3dvar_phy'] = False
config['wrfvar4']['use_obs_errfac'] = False
config['wrfvar7']['cv_options'] = 7
config['wrfvar7']['cloud_cv_options'] = 3
config['wrfvar7']['as1'] = [0.25, 0.75, 1.5]
config['wrfvar7']['as2'] = [0.25, 0.75, 1.5]
config['wrfvar7']['as3'] = [0.25, 0.75, 1.5]
config['wrfvar7']['as4'] = [0.25, 0.75, 1.5]
config['wrfvar7']['as5'] = [0.25, 0.75, 1.5]
config['wrfvar7']['rf_passes'] = 4
config['wrfvar7']['var_scaling1'] = 2.0
config['wrfvar7']['var_scaling2'] = 2.0
config['wrfvar7']['var_scaling3'] = 2.0
config['wrfvar7']['var_scaling4'] = 2.0
config['wrfvar7']['var_scaling5'] = 2.0
config['wrfvar7']['len_scaling1'] = 0.5
config['wrfvar7']['len_scaling2'] = 0.5
config['wrfvar7']['len_scaling3'] = 0.5
config['wrfvar7']['len_scaling4'] = 0.5
config['wrfvar7']['len_scaling5'] = 0.5
config['wrfvar7']['je_factor'] = 1.0
config['wrfvar12']['balance_type'] = 1
fg_d02 = f'{args.work_root}/wrfda/d02/wrfvar_output'
wrf.config_wrfda(args.work_root, args.wrfda_root, config, args, tag='radar', fg=fg_d02)
wrf.run_wrfda_3dvar(args.work_root, args.wrfda_root, config, args, tag='radar', fg=fg_d02)
run(f'ln -sf {args.work_root}/wrfda/d01 {args.work_root}/wrfda_radar/')

cli.banner('Run WRF warm forecast')
wrf.config_wrf(args.work_root, args.wrf_root, args.wrfda_root, config, args)
wrf.run_wrf(args.work_root, args.wrf_root, config, args, wrfda_work_dir=f'{args.work_root}/wrfda_radar')
