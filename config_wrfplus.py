#!/usr/bin/env python3

import argparse
import os
import pendulum
import f90nml
import re
from shutil import copy
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, parse_config, wrf_version, Version

def config_wrfplus(work_root, wrfplus_root, config, args):
	common_config = config['common']
	phys_config = config['physics'] if 'physics' in config else {}

	start_time = common_config['start_time']
	end_time = common_config['end_time']
	max_dom = common_config['max_dom']
	
	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wrf_work_dir = work_root + '/wrf'
	if not os.path.isdir(wrf_work_dir): cli.error(f'{wrf_work_dir} does not exist!')

	wrfplus_work_dir = work_root + '/wrfplus'
	if not os.path.isdir(wrfplus_work_dir): os.mkdir(wrfplus_work_dir)
	os.chdir(wrfplus_work_dir)

	version = wrf_version(wrfplus_root)

	wrf_namelist_input = f90nml.read(f'{wrf_work_dir}/namelist.input')

	cli.notice('Edit namelist.input for WRF.')
	copy(f'{wrfplus_root}/test/em_real/namelist.input', 'namelist.input')
	namelist_input = f90nml.read('namelist.input')
	namelist_input['time_control']['run_hours']              = common_config['forecast_hours']
	namelist_input['time_control']['start_year']             = [int(start_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['start_month']            = [int(start_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['start_day']              = [int(start_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['start_hour']             = [int(start_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['end_year']               = [int(end_time.format("Y")) for i in range(max_dom)]
	namelist_input['time_control']['end_month']              = [int(end_time.format("M")) for i in range(max_dom)]
	namelist_input['time_control']['end_day']                = [int(end_time.format("D")) for i in range(max_dom)]
	namelist_input['time_control']['end_hour']               = [int(end_time.format("H")) for i in range(max_dom)]
	namelist_input['time_control']['interval_seconds']       = wrf_namelist_input['time_control']['interval_seconds']
	namelist_input['time_control']['history_interval']       = wrf_namelist_input['time_control']['history_interval']
	namelist_input['time_control']['frames_per_outfile']     = 1
	namelist_input['time_control']['io_form_auxinput7']      = 2
	namelist_input['time_control']['iofields_filename']      = f'{wrfplus_root}/var/run/plus.io_config'
	namelist_input['time_control']['ignore_iofields_warning']= True
	# Copy from WRF namelist.input.
	for key in ('time_step', 'max_dom', 'e_we', 'e_sn', 'e_vert', 'p_top_requested', 'num_metgrid_levels', 'num_metgrid_soil_levels', 'dx', 'dy'):
		if key in wrf_namelist_input['domains']:
			namelist_input['domains'][key] = wrf_namelist_input['domains'][key]
	namelist_input['domains']     ['grid_id']                = [i + 1 for i in range(max_dom)]
	namelist_input['domains']     ['parent_id']              = common_config['parent_id']
	namelist_input['domains']     ['i_parent_start']         = common_config['i_parent_start']
	namelist_input['domains']     ['j_parent_start']         = common_config['j_parent_start']
	namelist_input['domains']     ['parent_grid_ratio']      = common_config['parent_grid_ratio']
	namelist_input['domains']     ['parent_time_step_ratio'] = common_config['parent_grid_ratio']
	namelist_input['physics']     ['mp_physics']             = 98
	namelist_input['physics']     ['mp_zero_out']            = 2
	namelist_input['physics']     ['ra_lw_physics']          = 0
	namelist_input['physics']     ['ra_sw_physics']          = 0
	namelist_input['physics']     ['sf_sfclay_physics']      = 0
	namelist_input['physics']     ['sf_surface_physics']     = wrf_namelist_input['physics']['sf_surface_physics']
	namelist_input['physics']     ['bl_pbl_physics']         = 98
	namelist_input['physics']     ['cu_physics']             = 0
	namelist_input['physics']     ['num_land_cat']           = wrf_namelist_input['physics']['num_land_cat'] if 'num_land_cat' in wrf_namelist_input['physics'] else 21
	namelist_input['dynamics']    ['dyn_opt']                = 302
	if version == Version('3.9.1'):
		namelist_input['dynamics']['max_rot_angle_gwd']  = 100
	# Delete some parameters.
	if 'eta_levels' in namelist_input['domains']:  del namelist_input['domains']['eta_levels']
	if 'iso_temp'   in namelist_input['dynamics']: del namelist_input['dynamics']['iso_temp']
	namelist_input.write('./namelist.input', force=True)
	
	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRFPLUS model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrfplus-root', dest='wrfplus_root', help='WRFPLUS root directory (e.g. WRFPLUS)')
	parser.add_argument('-w', '--work-root',  dest='work_root', help='Work root directory')
	parser.add_argument('-j', '--config-json', dest='config_json', help='Configuration JSON file.')
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

	config = parse_config(args.config_json)

	config_wrfplus(args.work_root, args.wrfplus_root, config, args)
