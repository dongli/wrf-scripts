#!/usr/bin/env python3

import argparse
import re
import os
import pexpect
import sys
sys.path.append('./utils')
from utils import edit_file, run, cli, check_files

parser = argparse.ArgumentParser(description="Build WRF model and its friends.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018 - All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-c', '--codes', help='Root directory of all codes (e.g. WRF, UPP)')
parser.add_argument('-w', '--wrf-root', dest='wrf_root', help='WRF root directory (e.g. WRF)')
parser.add_argument('-u', '--upp-root', dest='upp_root', help='UPP root directory (e.g. UPP)')
parser.add_argument('-s', '--compiler-suite', dest='compiler_suite', help='Compiler suite', choices=['gnu', 'pgi', 'intel'])
parser.add_argument('-f', '--force', help='Force to rebuild if already built', action='store_true')
args = parser.parse_args()

if not args.wrf_root:
	if os.getenv('WRF_ROOT'):
		args.wrf_root = os.getenv('WRF_ROOT')
	elif args.codes:
		args.wrf_root = args.codes + '/WRF'
	else:
		cli.error('Option --wrf-root or environment variable WRF_ROOT need to be set!')

if not args.upp_root:
	if os.getenv('UPP_ROOT'):
		args.upp_root = os.getenv('UPP_ROOT')
	elif args.codes:
		args.upp_root = args.codes + '/UPP'
	else:
		cli.error('Option --upp-root or environment variable UPP_ROOT need to be set!')

os.environ['WRF_DIR'] = args.wrf_root

os.chdir(args.upp_root)
if args.force: run('./clean -a &> /dev/null')
expected_exe_files = ('bin/copygb.exe', 'bin/ndate.exe', 'bin/unipost.exe')
if not check_files(expected_exe_files):
	cli.notice('Configure UPP ...')
	child = pexpect.spawn('./configure')
	child.expect('Enter selection.*')
	if args.compiler_suite == 'intel':
		child.sendline('4')
	elif args.compiler_suite == 'gnu':
		child.sendline('8')
	elif args.compiler_suite == 'pgi':
		child.sendline('14')
	child.wait()

	cli.notice('Compile UPP ...')
	run('./compile &> compile.out')

	if check_files(expected_exe_files):
		cli.notice('Succeeded.')
	else:
		cli.error(f'Failed! Check {args.upp_root}/compile.out')
else:
	cli.notice('UPP is already built.')
