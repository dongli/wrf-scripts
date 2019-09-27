#! /usr/bin/env python3

import argparse
import os
import pendulum
import f90nml
import re
from netCDF4 import Dataset
from io import StringIO
from shutil import copyfile
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/../utils')
from utils import cli, parse_config, wrf_version, Version

def config_wrfda(work_root, wrfda_root, config, args, wrf_work_dir=None):
	start_time = config['custom']['start_time']
	end_time = config['custom']['end_time']
	datetime_fmt  = 'YYYY-MM-DD_HH:mm:ss'
	start_time_str = start_time.format(datetime_fmt)
	max_dom = config['domains']['max_dom']

	# Need to take some parameters from wrfinput file.
	if not wrf_work_dir: wrf_work_dir = work_root + '/wrf'
	if not os.path.isdir(wrf_work_dir): cli.error(f'{wrf_work_dir} does not exist!')

	if max_dom > 1:
		if not 'run_wrfda_on_dom' in config['custom']:
			cli.error('You need to set run_wrfda_on_dom to set which domain to work on!')
		dom_idx = config['custom']['run_wrfda_on_dom']
		dom_str = 'd' + str(dom_idx + 1).zfill(2)
		wrfda_work_dir = os.path.abspath(work_root) + f'/wrfda/{dom_str}'
	else:
		dom_idx = 0
		dom_str = 'd01'
		wrfda_work_dir = os.path.abspath(work_root) + '/wrfda'
	if not os.path.isdir(wrfda_work_dir): os.makedirs(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	version = wrf_version(wrfda_root)

	wrfinput = Dataset(f'{wrf_work_dir}/wrfinput_{dom_str}_{start_time_str}')
	num_land_cat = wrfinput.getncattr('NUM_LAND_CAT')
	hypsometric_opt = wrfinput.getncattr('HYPSOMETRIC_OPT')
	wrfinput.close()

	try:
		time_window = config['custom']['wrfda']['time_window']
	except:
		time_window = 360
	# Read in namelist template (not exact Fortran namelist format, we need to change it).
	template = open(f'{wrfda_root}/var/README.namelist').read()
	template = re.sub(r'^[^&]*', '', template, flags=re.DOTALL)
	template = re.sub(r';.*', '', template)
	template = re.sub(r'\([^\)]*\)', '', template)
	namelist_input = f90nml.read(StringIO(template))
	namelist_input['wrfvar1']['var4d_lbc'] = False
	namelist_input['wrfvar18']['analysis_date'] = start_time_str
	namelist_input['wrfvar21']['time_window_min'] = start_time.subtract(minutes=time_window/2).format(datetime_fmt)
	namelist_input['wrfvar22']['time_window_max'] = start_time.add(minutes=time_window/2).format(datetime_fmt)
	# Fix bugs
	namelist_input['wrfvar2']['qc_rej_both'] = False
	namelist_input['wrfvar14']['rtminit_satid'] = -1
	namelist_input['wrfvar14']['rtminit_sensor'] = -1
	if version == Version('3.6.1'):
		namelist_input['wrfvar4']['use_iasiobs'] = False
		del namelist_input['wrfvar4']['use_iasisobs']
		namelist_input['wrfvar4']['use_seviriobs'] = False
		del namelist_input['wrfvar4']['use_sevirisobs']
		namelist_input['wrfvar5']['max_omb_spd'] = namelist_input['wrfvar5']['max_omb_sp']
		del namelist_input['wrfvar5']['max_omb_sp']
		namelist_input['wrfvar5']['max_error_spd'] = namelist_input['wrfvar5']['max_error_sp']
		del namelist_input['wrfvar5']['max_error_sp']
	elif version > Version('3.8.1'):
		namelist_input['wrfvar11']['write_detail_grad_fn'] = True
	namelist_input['wrfvar11']['calculate_cg_cost_fn'] = True
	# Merge namelist.input in tutorial.
	tmp = f90nml.read(f'{wrfda_root}/var/test/tutorial/namelist.input')
	for key, value in tmp.items():
		if not key in namelist_input:
			namelist_input[key] = value
	namelist_input['time_control']['run_hours'         ] = config['custom']['forecast_hours']
	namelist_input['time_control']['start_year'        ] = [int(start_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['start_month'       ] = [int(start_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['start_day'         ] = [int(start_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['start_hour'        ] = [int(start_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['end_year'          ] = [int(end_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['end_month'         ] = [int(end_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['end_day'           ] = [int(end_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['end_hour'          ] = [int(end_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['frames_per_outfile'] = [1 for i in range(max_dom)]
	for key, value in config['time_control'].items(): namelist_input['time_control'][key] = value
	for key, value in config['domains'     ].items(): namelist_input['domains'     ][key] = value
	# WRFDA only take grids parameters one domain at a time.
	namelist_input['domains']['max_dom']                     = 1
	for key in ('e_we', 'e_sn', 'e_vert', 'dx', 'dy', 'grid_id', 'parent_id', 'i_parent_start', 'j_parent_start', 'parent_grid_ratio', 'parent_time_step_ratio'):
		if key in config['domains']:
			namelist_input['domains'][key] = config['domains'][key][dom_idx]
	namelist_input['domains']['hypsometric_opt'] = hypsometric_opt
	# Sync physics parameters.
	if 'physics' in config:
		for key, value in config['physics'].items():
			namelist_input['physics'][key] = value
	namelist_input['physics']['num_land_cat'] = num_land_cat
	if version == Version('3.9.1'):
		namelist_input['dynamics']['gwd_opt'] = 0
	# Write customized parameters.
	for tag in range(1, 23):
		section = f'wrfvar{tag}'
		for key, value in config[section].items():
			namelist_input[section][key] = value

	namelist_input.write(f'{wrfda_work_dir}/namelist.input', force=True)

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRFDA system.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')	
	parser.add_argument('-w', '--work-root', dest='work_root', help='Work root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	args = parser.parse_args()

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

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or enviroment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

	config = parse_config(args.config_json)

	config_wrfda(args.work_root, args.wrfda_root, config, args)
