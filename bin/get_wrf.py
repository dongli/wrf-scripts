#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import Version, run, cli, check_files

parser = argparse.ArgumentParser(description='Get WRF and its friends.', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--wrf-version', dest='wrf_version')
parser.add_argument('--wps-version', dest='wps_version')
args = parser.parse_args()

if args.wrf_version:
	cli.notice(f'Get WRF {args.wrf_version} ...')
	wrf_version = Version(args.wrf_version)
	if wrf_version >= Version('4.0'):
		run(f'wget -c https://github.com/wrf-model/WRF/archive/v{wrf_version}.tar.gz -O wrf-{wrf_version}.tar.gz')
	else:
		run(f'wget -c https://github.com/wrf-model/WRF/archive/V{wrf_version}.tar.gz -O wrf-{wrf_version}.tar.gz')
		run(f'wget -c https://www2.mmm.ucar.edu/wrf/src/WRFDA_V{wrf_version}.tar.gz')
		if wrf_version == Version('3.6.1'):
			run('wget -c https://www2.mmm.ucar.edu/wrf/users/wrfda/download/WRFPLUS_V3.6.1_r7511.tar.gz')
		else:
			run(f'wget -c https://www2.mmm.ucar.edu/wrf/src/WRFPLUS_V{wrf_version}.tar.gz')
if args.wps_version:
	wps_version = Version(args.wps_version)
	if wps_version >= Version('4.0'):
		run(f'wget -c https://github.com/wrf-model/WPS/archive/v{wps_version}.tar.gz -O wps-{wps_version}.tar.gz')
