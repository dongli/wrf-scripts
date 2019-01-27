#! /usr/bin/env python3

import argparse
import os
import pendulum
import f90nml
import re
from shutil import copyfile
from pprint import pprint
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{script_root}/utils')
from utils import cli, parse_config

def config_wrfvar(wrfda_root, work_root, config, args):
	pprint(config)
	common_config = config['common']
	if not 'wrfda' in config:
		cli.error('There is no "wrfda" in configuration file!')
	wrfda_config = config['wrfda']

	start_time = common_config['start_time']
	end_time   = common_config['end_time']
	datetime_fmt  = 'YYYY-MM-DD_HH:mm:ss.0000'	

	wrfda_work_dir = os.path.abspath(work_root) + '/WRFDA'
	if not os.path.isdir(wrfda_work_dir): os.mkdir(wrfda_work_dir)
	os.chdir(wrfda_work_dir)

	time_window  = config['wrfda']['time_window'] if 'time_window' in config['wrfda'] else 360
	namelist_input = f90nml.read(f'{wrfda_root}/var/test/tutorial/namelist.input')
	# wrfvar1
	namelist_input['wrfvar1']['update_sfcdiags']              = False
	namelist_input['wrfvar1']['use_wrf_sfcinfo']              = True
	namelist_input['wrfvar1']['use_background_errors']        = True
	namelist_input['wrfvar1']['write_iv_gpsztd']              = False
	namelist_input['wrfvar1']['write_increments']             = False
	namelist_input['wrfvar1']['var4d']                        = wrfda_config['type'] == '4dvar'
	namelist_input['wrfvar1']['var4d_lbc']                    = True
	namelist_input['wrfvar1']['var4d_bin']                    = 3600
	namelist_input['wrfvar1']['var4d_bin_rain']               = 3600
	namelist_input['wrfvar1']['multi_inc']                    = 0
	namelist_input['wrfvar1']['print_detail_radar']           = False
	namelist_input['wrfvar1']['print_detail_rain']            = False
	namelist_input['wrfvar1']['print_detail_rad']             = False
	namelist_input['wrfvar1']['print_detail_xa']              = False
	namelist_input['wrfvar1']['print_detail_xb']              = False
	namelist_input['wrfvar1']['print_detail_obs']             = False
	namelist_input['wrfvar1']['print_detail_map']             = False
	namelist_input['wrfvar1']['print_detail_grad']            = False
	namelist_input['wrfvar1']['print_detail_outerloop']       = False
	namelist_input['wrfvar1']['check_max_iv_print']           = True
	# wrfvar2
	namelist_input['wrfvar2']['analysis_accu']                = 900
	namelist_input['wrfvar2']['calc_w_increment']             = False
	namelist_input['wrfvar2']['dt_cloud_model']               = False
	namelist_input['wrfvar2']['wind_sd']                      = False
	namelist_input['wrfvar2']['wind_sd_buoy']                 = False
	namelist_input['wrfvar2']['wind_sd_synop']                = False
	namelist_input['wrfvar2']['wind_sd_ships']                = False
	namelist_input['wrfvar2']['wind_sd_metar']                = False
	namelist_input['wrfvar2']['wind_sd_sound']                = False
	namelist_input['wrfvar2']['wind_sd_pilot']                = False
	namelist_input['wrfvar2']['wind_sd_airep']                = False
	namelist_input['wrfvar2']['wind_sd_qscat']                = False
	namelist_input['wrfvar2']['wind_sd_tamdar']               = False
	namelist_input['wrfvar2']['wind_sd_geoamv']               = False
	namelist_input['wrfvar2']['wind_sd_mtgirs']               = False
	namelist_input['wrfvar2']['wind_sd_polaramv']             = False
	namelist_input['wrfvar2']['wind_sd_profiler']             = False
	namelist_input['wrfvar2']['wind_stats_sd']                = False
	namelist_input['wrfvar2']['qc_rej_both']                  = False
	# wrfvar3
	namelist_input['wrfvar3']['fg_format']                    = 1
	namelist_input['wrfvar3']['ob_format']                    = 2
	namelist_input['wrfvar3']['ob_format_gpsro']              = 2
	namelist_input['wrfvar3']['num_fgat_time']                = 1
	# wrfvar4
	namelist_input['wrfvar4']['thin_conv']                    = True
	namelist_input['wrfvar4']['thin_conv_ascii']              = False
	namelist_input['wrfvar4']['thin_mesh_conv']               = 20.0
	namelist_input['wrfvar4']['use_synopobs']                 = True
	namelist_input['wrfvar4']['use_shipsobs']                 = True
	namelist_input['wrfvar4']['use_metarobs']                 = True
	namelist_input['wrfvar4']['use_soundobs']                 = True
	namelist_input['wrfvar4']['use_pilotobs']                 = True
	namelist_input['wrfvar4']['use_airepobs']                 = True
	namelist_input['wrfvar4']['use_geoamvobs']                = True
	namelist_input['wrfvar4']['use_polaramvobs']              = True
	namelist_input['wrfvar4']['use_bogusobs']                 = True
	namelist_input['wrfvar4']['use_buoyobs']                  = True
	namelist_input['wrfvar4']['use_profilerobs']              = True
	namelist_input['wrfvar4']['use_satemobs']                 = True
	namelist_input['wrfvar4']['use_gpspwobs']                 = True
	namelist_input['wrfvar4']['use_gpsztdobs']                = False
	namelist_input['wrfvar4']['use_gpsrefobs']                = True
	namelist_input['wrfvar4']['use_gpsephobs']                = False
	namelist_input['wrfvar4']['top_km_gpsro']                 = 30.0
	namelist_input['wrfvar4']['bot_km_gpsro']                 = 0.0
	namelist_input['wrfvar4']['use_qscatobs']                 = True
	namelist_input['wrfvar4']['use_radarobs']                 = False
	namelist_input['wrfvar4']['use_radar_rv']                 = False
	namelist_input['wrfvar4']['use_radar_rf']                 = False
	namelist_input['wrfvar4']['use_radar_rhv']                = False
	namelist_input['wrfvar4']['use_radar_rqv']                = False
	namelist_input['wrfvar4']['use_rainobs']                  = False
	namelist_input['wrfvar4']['thin_rainobs']                 = True
	namelist_input['wrfvar4']['use_airsretobs']               = True
	namelist_input['wrfvar4']['use_hirs2obs']                 = False
	namelist_input['wrfvar4']['use_hirs3obs']                 = False
	namelist_input['wrfvar4']['use_hirs4obs']                 = False
	namelist_input['wrfvar4']['use_mhsobs']                   = False
	namelist_input['wrfvar4']['use_mhuobs']                   = False
	namelist_input['wrfvar4']['use_amsuaobs']                 = False
	namelist_input['wrfvar4']['use_amsubobs']                 = False
	namelist_input['wrfvar4']['use_airsobs']                  = False
	namelist_input['wrfvar4']['use_eos_amsuaobs']             = False
	namelist_input['wrfvar4']['use_ssmisobs']                 = False
	namelist_input['wrfvar4']['use_atmsobs']                  = False
	namelist_input['wrfvar4']['use_iasiobs']                  = False
	namelist_input['wrfvar4']['use_seviriobs']                = False
	namelist_input['wrfvar4']['use_amsr2obs']                 = False
	namelist_input['wrfvar4']['use_goesimgobs']               = False
	namelist_input['wrfvar4']['use_obs_errfac']               = False
	# wrfvar5
	namelist_input['wrfvar5']['check_max_iv']                 = True
	namelist_input['wrfvar5']['max_error_t']                  = 5.0
	namelist_input['wrfvar5']['max_error_uv']                 = 5.0
	namelist_input['wrfvar5']['max_error_pw']                 = 5.0
	namelist_input['wrfvar5']['max_error_ref']                = 5.0
	namelist_input['wrfvar5']['max_error_eph']                = 5.0
	namelist_input['wrfvar5']['max_error_q']                  = 5.0
	namelist_input['wrfvar5']['max_error_p']                  = 5.0
	namelist_input['wrfvar5']['max_error_thickness']          = 5.0
	namelist_input['wrfvar5']['max_error_rv']                 = 5.0
	namelist_input['wrfvar5']['max_error_rf']                 = 5.0
	namelist_input['wrfvar5']['max_error_rain']               = 5.0
	namelist_input['wrfvar5']['max_omb_spd']                  = 100.0
	namelist_input['wrfvar5']['max_omb_dir']                  = 1000.0
	namelist_input['wrfvar5']['max_error_spd']                = 5.0
	namelist_input['wrfvar5']['max_error_dir']                = 5.0
	namelist_input['wrfvar5']['put_rand_seed']                = False
	# wrfvar6
	namelist_input['wrfvar6']['max_ext_its']                  = 1
	namelist_input['wrfvar6']['ntmax']                        = 75
	namelist_input['wrfvar6']['eps']                          = 0.01
	namelist_input['wrfvar6']['orthonorm_gradient']           = False
	# wrfvar7
	namelist_input['wrfvar7']['cv_options']                   = wrfda_config['cv_options']
	namelist_input['wrfvar7']['as1']                          = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as2']                          = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as3']                          = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as4']                          = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['as5']                          = [0.25, 1.0, 1.5]
	namelist_input['wrfvar7']['rf_passes']                    = 6
	namelist_input['wrfvar7']['var_scaling1']                 = 1.0
	namelist_input['wrfvar7']['var_scaling2']                 = 1.0
	namelist_input['wrfvar7']['var_scaling3']                 = 1.0
	namelist_input['wrfvar7']['var_scaling4']                 = 1.0
	namelist_input['wrfvar7']['var_scaling5']                 = 1.0
	namelist_input['wrfvar7']['var_scaling6']                 = 1.0
	namelist_input['wrfvar7']['len_scaling1']                 = 1.0
	namelist_input['wrfvar7']['len_scaling2']                 = 1.0
	namelist_input['wrfvar7']['len_scaling3']                 = 1.0
	namelist_input['wrfvar7']['len_scaling4']                 = 1.0
	namelist_input['wrfvar7']['len_scaling5']                 = 1.0
	namelist_input['wrfvar7']['len_scaling6']                 = 1.0
	namelist_input['wrfvar7']['len_scaling7']                 = 1.0
	namelist_input['wrfvar7']['len_scaling8']                 = 1.0
	namelist_input['wrfvar7']['len_scaling9']                 = 1.0
	namelist_input['wrfvar7']['len_scaling10']                = 1.0
	namelist_input['wrfvar7']['len_scaling11']                = 1.0
	namelist_input['wrfvar7']['je_factor']                    = 1.0
	namelist_input['wrfvar7']['cloud_cv_options']             = 0
	# wrfvar8
	namelist_input['wrfvar8']                                 = {}
	# wrfvar9
	namelist_input['wrfvar9']['stdout']                       = 6
	namelist_input['wrfvar9']['stderr']                       = 0
	namelist_input['wrfvar9']['trace_unit']                   = 7
	namelist_input['wrfvar9']['trace_pe']                     = 0
	namelist_input['wrfvar9']['trace_repeat_head']            = 10
	namelist_input['wrfvar9']['trace_repeat_body']            = 10
	namelist_input['wrfvar9']['trace_max_depth']              = 30
	namelist_input['wrfvar9']['trace_use']                    = False
	namelist_input['wrfvar9']['trace_use_frequent']           = False
	namelist_input['wrfvar9']['trace_use_dull']               = False
	namelist_input['wrfvar9']['trace_use_memory']             = True
	namelist_input['wrfvar9']['trace_all_pes']                = False
	namelist_input['wrfvar9']['trace_csv']                    = True
	namelist_input['wrfvar9']['use_html']                     = True
	namelist_input['wrfvar9']['warnings_are_fatal']           = False
	# wrfvar10
	namelist_input['wrfvar10']['test_transforms']             = False
	namelist_input['wrfvar10']['test_gradient']               = False
	# wrfvar11
	namelist_input['wrfvar11']['cv_options_hum']              = 1
	namelist_input['wrfvar11']['check_rh']                    = 0
	namelist_input['wrfvar11']['sfc_assi_options']            = 1
	namelist_input['wrfvar11']['sfc_stheight_diff']           = 100.0
	namelist_input['wrfvar11']['sfc_stheight_diff_ztd']       = 1000.0
	namelist_input['wrfvar11']['consider_xap4ztd']            = True
	namelist_input['wrfvar11']['obs_err_inflate']             = False
	namelist_input['wrfvar11']['stn_ht_diff_scale']           = 200.0
	namelist_input['wrfvar11']['psfc_from_slp']               = False
	namelist_input['wrfvar11']['calculate_cg_cost_fn']        = False
	namelist_input['wrfvar11']['write_detal_grad_fn']         = False
	namelist_input['wrfvar11']['seed_array1']                 = 1
	namelist_input['wrfvar11']['seed_array2']                 = 1
	# wrfvar12
	namelist_input['wrfvar12']['use_wpec']                    = False
	namelist_input['wrfvar12']['wpec_factor']                 = 0.001
	namelist_input['wrfvar12']['balance_type']                = 3
	namelist_input['wrfvar12']['use_divc']                    = False
	namelist_input['wrfvar12']['divc_factor']                 = 1000.0
	namelist_input['wrfvar12']['use_lsac']                    = False
	namelist_input['wrfvar12']['lsac_nh_step']                = 1
	namelist_input['wrfvar12']['lsac_nv_step']                = 1
	namelist_input['wrfvar12']['lsac_nv_start']               = 1
	namelist_input['wrfvar12']['lsac_use_u']                  = True
	namelist_input['wrfvar12']['lsac_use_v']                  = True
	namelist_input['wrfvar12']['lsac_use_t']                  = True
	namelist_input['wrfvar12']['lsac_use_q']                  = True
	namelist_input['wrfvar12']['lsac_u_error']                = 2.5
	namelist_input['wrfvar12']['lsac_v_error']                = 2.5
	namelist_input['wrfvar12']['lsac_t_error']                = 2.0
	namelist_input['wrfvar12']['lsac_q_error']                = 0.002
	namelist_input['wrfvar12']['lsac_print_details']          = False

	namelist_input.write(f'{wrfda_work_dir}/namelist.input', force=True)

	cli.notice('Succeeded.')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, WPS)')
	parser.add_argument('-d', '--wrfda-root', dest='wrfda_root', help='WRFDA root directory (e.g. WRFDA)')	
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

	if not args.work_root:
		if os.getenv('WORK_ROOT'):
			args.work_root = os.getenv('WORK_ROOT')
		else:
			cli.error('Option --work-root or enviroment variable WORK_ROOT need to be set!')
	args.work_root = os.path.abspath(args.work_root)
	if not os.path.isdir(args.work_root):
		cli.error(f'Directory {args.work_root} does not exist!')

	config = parse_config(args.config_json)

	config_wrfvar(args.wrfda_root, args.work_root, config, args)
