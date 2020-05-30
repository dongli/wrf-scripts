#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/../utils')
from utils import Version, run, cli, check_files

parser = argparse.ArgumentParser(description='Get UPP.', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--upp-version', dest='upp_version')
args = parser.parse_args()

args.upp_version = Version(args.upp_version)

cli.notice(f'Get UPP {args.upp_version} ...')

if args.upp_version >= Version('4.1'):
	run(f'wget -c https://github.com/NCAR/NCEPlibs/archive/upp_v{args.upp_version}_release.tar.gz')
	run(f'wget -c https://dtcenter.org/dfiles/code/upp/DTC_upp_v{args.upp_version}.tar.gz')
else:
	run(f'wget -c https://dtcenter.org/sites/default/files/code/DTC_upp_v{args.upp_version}.tar.gz')
