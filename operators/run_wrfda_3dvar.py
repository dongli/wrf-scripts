#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import re
import sys
import config_wrfda
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import cli, check_files, search_files, run, submit_job, parse_config

scripts_root = os.path.dirname(os.path.realpath(__file__))

def run_wrfda_3dvar(work_root, wrfda_root, config, args, wrf_work_dir=None, force=False, tag=None, fg=None):
	start_time = config['custom']['start_time']
	datetime_fmt = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)
	max_dom = config['domains']['max_dom']

	if not wrf_work_dir:
		if tag != None:
			wrf_work_dir = f'{work_root}/wrf_{tag}'
		else:
			wrf_work_dir = f'{work_root}/wrf'
	if not os.path.isdir(wrf_work_dir): cli.error(f'{wrf_work_dir} does not exist!')

	if tag != None:
		obsproc_work_dir = f'{work_root}/wrfda_{tag}/obsproc'
	else:
		obsproc_work_dir = f'{work_root}/wrfda/obsproc'
	if not os.path.isdir(obsproc_work_dir): cli.error(f'{obsproc_work_dir} does not exist!')

	if max_dom > 1:
		dom_str = 'd' + str(config['custom']['wrfda']['dom'] + 1).zfill(2)
		if tag != None:
			wrfda_work_dir = f'{work_root}/wrfda_{tag}/{dom_str}'
		else:
			wrfda_work_dir = f'{work_root}/wrfda/{dom_str}'
	else:
		dom_str = 'd01'
		if tag != None:
			wrfda_work_dir = f'{work_root}/wrfda_{tag}'
		else:
			wrfda_work_dir = f'{work_root}/wrfda'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	be_work_dir = os.path.dirname(os.path.abspath(work_root)) + '/be/' + dom_str

	if os.path.isfile(f'wrfvar_output_{start_time_str}') and not args.force and not force:
		run(f'ls -l wrfvar_output_{start_time_str}')
		cli.notice(f'wrfvar_output_{start_time_str} already exist.')
		return

	run(f'ln -sf {wrfda_root}/run/LANDUSE.TBL {wrfda_work_dir}')

	if not os.path.isfile('namelist.input'):
		cli.error('namelist.input has not been generated! Run config_wrfda.py.')

	# BE matrix
	if 'cv_options' in config['wrfvar7']:
		if config['wrfvar7']['cv_options'] == 5:
			if not os.path.isfile(f'{be_work_dir}/be.dat.cv5'):
				cli.error(f'BE matrix {be_work_dir}/be.dat.cv5 does not exist!')
			run(f'ln -sf {be_work_dir}/be.dat.cv5 be.dat')
		elif config['wrfvar7']['cv_options'] == 6:
			if not os.path.isfile(f'{be_work_dir}/be.dat.cv6'):
				cli.error(f'BE matrix {be_work_dir}/be.dat.cv6 does not exist!')
			run(f'ln -sf {be_work_dir}/be.dat.cv6 be.dat')
		elif config['wrfvar7']['cv_options'] == 7:
			if not os.path.isfile(f'{be_work_dir}/be.dat.cv7'):
				cli.error(f'BE matrix {be_work_dir}/be.dat.cv7 does not exist!')
			run(f'ln -sf {be_work_dir}/be.dat.cv7 be.dat')
	if not os.path.exists('./be.dat'):
		run(f'ln -sf {wrfda_root}/var/run/be.dat.cv3 be.dat')

	# First guess
	expected_files = ['{}/wrfinput_d{:02d}_{}'.format(wrf_work_dir, i + 1, start_time_str) for i in range(max_dom)]
	if not check_files(expected_files):
		cli.error('real.exe or da_update_bc.exe wasn\'t executed successfully!')
	# TODO: Assume there is only one domain to be assimilated.
	if fg != None:
		run(f'ln -sf {fg} {wrfda_work_dir}/fg')
	else:
		run(f'ln -sf {wrf_work_dir}/wrfinput_{dom_str}_{start_time_str} {wrfda_work_dir}/fg')

	# Observation data
	if config['custom']['wrfda']['type'] == '3dvar':
		if 'use_radarobs' in config['wrfvar4'] and config['wrfvar4']['use_radarobs']:
			# Radar data
			run(f'rm -f ob.*')
			for obs_radar_file in glob(f'{args.littler_root}/{start_time.format("YYYYMMDD")}/obs.radar.*'):
				radar_time = pendulum.from_format(os.path.basename(obs_radar_file).split('.')[2], 'YYYYMMDDHHmm')
				if radar_time == start_time:
					run(f'ln -sf {obs_radar_file} ob.radar')
			if os.path.isfile(f'wrfvar_output_{start_time_str}'):
				cli.notice('Use previous analysis data as the background.')
				run(f'mv wrfvar_output_{start_time_str} wrfvar_output_conv_{start_time_str}')
				run(f'ln -sf wrfvar_output_conv_{start_time_str} fg')
		elif config['wrfvar3']['ob_format'] == 2 and os.path.isfile(f'{obsproc_work_dir}/obs_gts_{start_time.format(datetime_fmt)}.3DVAR'):
			# LITTLE_R conventional data
			run(f'ln -sf {obsproc_work_dir}/obs_gts_{start_time.format(datetime_fmt)}.3DVAR ob.ascii')
		elif config['wrfvar3']['ob_format'] == 1 and config['custom']['wrfda']['prepbufr_source'] == 'gdas':
			# PREPBUFR conventional data
			gdas_file_path = f'{args.prepbufr_root}/gdas.{start_time.format("YYYYMMDD")}/gdas.t{start_time.hour:02}z.prepbufr.nr'
			if not os.path.isfile(gdas_file_path):
				cli.error(f'{gdas_file_path} does not exist!')
			run(f'ln -sf {gdas_file_path} ob.bufr')

	if os.path.isfile(f'{wrfda_work_dir}/wrfvar_output_{start_time_str}') and not args.force:
		cli.notice(f'{wrfda_work_dir}/wrfvar_output_{start_time_str} already exists.')
		return

	cli.stage(f'Run da_wrfvar.exe at {wrfda_work_dir} ...')
	submit_job(f'{wrfda_root}/var/build/da_wrfvar.exe', args.np, config, args, wait=True)

	expected_files = [f'wrfvar_output', 'statistics']
	if not check_files(expected_files):
		# Check if the failure is caused by parallel computing? Such as cv_options is zero in some process.
		if search_files('rsl.error.*', 'Invalid CV option chosen:  cv_options =    0'):
			cli.warning('Failed to run da_wrfvar.exe in parallel. Try to run in serial.')
			submit_job(f'{wrfda_root}/var/build/da_wrfvar.exe', 1, config, args, wait=True)
			if not check_files(expected_files):
				cli.error(f'Still failed! See {wrfda_work_dir}/rsl.error.0000.')
		else:
			cli.error(f'Failed! See {wrfda_work_dir}/rsl.error.0000.')
	else:
		print(open('statistics').read())
		run(f'ncl -Q {scripts_root}/../plots/plot_cost_grad_fn.ncl')
		run(f'cp wrfvar_output wrfvar_output_{start_time_str}')
		cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRFDA 3DVar system.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS, WRFDA)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')    
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument(      '--wrf-work-dir', dest='wrf_work_dir', help='Work directory of WRF')
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

	if args.wrf_work_dir: args.wrf_work_dir = os.path.abspath(args.wrf_work_dir)

	config = parse_config(args.config_json)

	run_wrfda_3dvar(args.work_root, args.wrfda_root, config, args, args.wrf_work_dir)
