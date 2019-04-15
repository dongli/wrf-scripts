#!/usr/bin/env python3

import argparse
from glob import glob
import os
import pendulum
import f90nml
import re
from math import radians, cos, sin, asin, sqrt
from shutil import copy
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, parse_config, wrf_version, Version

def config_wrf(work_root, wrf_root, wrfda_root, config, args):
	common_config = config['common']
	phys_config = config['physics'] if 'physics' in config else {}

	start_time = common_config['start_time']
	end_time = common_config['end_time']
	max_dom = common_config['max_dom']
	
	start_time_str = start_time.format('YYYY-MM-DD_HH:mm:ss')
	end_time_str = end_time.format('YYYY-MM-DD_HH:mm:ss')

	wrf_work_dir = work_root + '/wrf'
	if not os.path.isdir(wrf_work_dir): os.mkdir(wrf_work_dir)
	os.chdir(wrf_work_dir)

	version = wrf_version(wrf_root)

	cli.notice('Edit namelist.input for WRF.')
	copy(f'{wrf_root}/run/namelist.input', 'namelist.input')
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
	namelist_input['time_control']['frames_per_outfile']     = 1
	namelist_input['domains']     ['time_step']              = int(common_config['time_step'])
	namelist_input['domains']     ['max_dom']                = max_dom
	namelist_input['domains']     ['e_we']                   = common_config['e_we']
	namelist_input['domains']     ['e_sn']                   = common_config['e_sn']
	namelist_input['domains']     ['dx']                     = [common_config['dx'][i] / common_config['parent_grid_ratio'][i] for i in range(max_dom)]
	namelist_input['domains']     ['dy']                     = [common_config['dy'][i] / common_config['parent_grid_ratio'][i] for i in range(max_dom)]
	namelist_input['domains']     ['grid_id']                = [i + 1 for i in range(max_dom)]
	namelist_input['domains']     ['parent_id']              = common_config['parent_id']
	namelist_input['domains']     ['i_parent_start']         = common_config['i_parent_start']
	namelist_input['domains']     ['j_parent_start']         = common_config['j_parent_start']
	namelist_input['domains']     ['parent_grid_ratio']      = common_config['parent_grid_ratio']
	namelist_input['domains']     ['parent_time_step_ratio'] = common_config['parent_grid_ratio']
	if 'physics_suite' in namelist_input['physics']: del namelist_input['physics']['physics_suite']
	namelist_input['physics']     ['mp_physics']             = phys_config['mp']          if 'mp'          in phys_config else 8
	namelist_input['physics']     ['mp_zero_out']            = phys_config['mp_zero_out'] if 'mp_zero_out' in phys_config else 2
	namelist_input['physics']     ['ra_lw_physics']          = phys_config['ra_lw']       if 'ra_lw'       in phys_config else 4
	namelist_input['physics']     ['ra_sw_physics']          = phys_config['ra_sw']       if 'ra_sw'       in phys_config else 4
	namelist_input['physics']     ['radt']                   = phys_config['radt']        if 'radt'        in phys_config else common_config['dx'][0] / 1000
	namelist_input['physics']     ['sf_sfclay_physics']      = phys_config['sf_sfclay']   if 'sf_sfclay'   in phys_config else 1
	namelist_input['physics']     ['sf_surface_physics']     = phys_config['sf_surface']  if 'sf_surface'  in phys_config else 2
	namelist_input['physics']     ['bl_pbl_physics']         = phys_config['bl_pbl']      if 'bl_pbl'      in phys_config else 1
	namelist_input['physics']     ['bldt']                   = phys_config['bldt']        if 'bldt'        in phys_config else 0
	namelist_input['physics']     ['cu_physics']             = phys_config['cu']          if 'cu'          in phys_config else 3
	namelist_input['physics']     ['cudt']                   = phys_config['cudt']        if 'cudt'        in phys_config else 0
	if version == Version('3.9.1'):
		namelist_input['dynamics']['max_rot_angle_gwd']  = 100
	# namelist_input['dynamics']    ['epssm']                  = 0.3
	# namelist_input['dynamics']    ['w_damping']              = 1
	namelist_input.write('./namelist.input', force=True)
	
	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Configure WRF model.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument(      '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
	parser.add_argument(      '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')
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

	if not args.wrfda_root:
		if os.getenv('WRFDA_ROOT'):
			args.wrfda_root = os.getenv('WRFDA_ROOT')
		elif args.codes:
			args.wrfda_root = args.codes + '/WRFDA'
		else:
			cli.error('Option --wrf-root or environment variable WRFDA_ROOT need to be set!')
	args.wrfda_root = os.path.abspath(args.wrfda_root)
	if not os.path.isdir(args.wrfda_root):
		cli.error(f'Directory {args.wrfda_root} does not exist!')

	config = parse_config(args.config_json)

	config_wrf(args.work_root, args.wrf_root, args.wrfda_root, config, args)
