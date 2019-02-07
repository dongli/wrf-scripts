#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import cli, parse_config
import wrf_operators as wrf

parser = argparse.ArgumentParser(description="Run WRF model by hiding operation details.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
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

wrf.config_wps(args.work_root, args.wps_root, args.geog_root, config, args)
wrf.config_wrf(args.work_root, args.wrf_root, config, args)
wrf.run_wps(args.work_root, args.wps_root, args.bkg_root, config, args)
wrf.run_real(args.work_root, args.prod_root, args.wrf_root, config, args)
wrf.config_wrfda(args.work_root, args.wrfda_root, config, args)
wrf.run_wrfda_obsproc(args.work_root, args.prod_root, args.wrfda_root, args.littler_root, config, args)
wrf.run_wrfda_3dvar(args.work_root, args.prod_root, args.wrfda_root, config, args)
wrf.run_wrfda_update_bc(args.work_root, args.prod_root, args.wrfda_root, False, config, args)
wrf.run_wrf(args.work_root, args.prod_root, args.wrf_root, config, args)
