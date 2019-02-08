#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append(f'{os.path.dirname(os.path.realpath(__file__))}/utils')
from utils import parse_time, run, cli, check_files

scripts_root = os.path.dirname(os.path.realpath(__file__))

def convert_gdas(gdas_root, littler_root, time, args):
	gdas_file_path = f'{gdas_root}/{time.format("YYYYMMDD")}/' + 'gdas.t{:02d}z.prepbufr.nr'.format(time.hour)
	if not os.path.isfile(gdas_file_path):
		cli.error(f'File {gdas_file_path} does not exist!')
	cmd = f'{scripts_root}/lib/data-translators/build/data_translate.exe'
	if not os.path.isfile(cmd):
		cli.error(f'Executable {cmd} has not been built!')
	obs_files = []
	for obs_type in ('synop', 'metar', 'raob', 'amdar', 'profiler', 'ship'):
		obs_file = f'/tmp/obs.{obs_type}.{time.format("YYYYMMDDHHmm")}'
		if args.verbose:
			run(f'{cmd} -r {obs_type}_prepbufr -w littler -i {gdas_file_path} -o {obs_file}')
		else:
			run(f'{cmd} -r {obs_type}_prepbufr -w littler -i {gdas_file_path} -o {obs_file} &> /dev/null')
		obs_files.append(obs_file)
	run(f'cat {" ".join(obs_files)} > {littler_root}/obs.{time.format("YYYYMMDDHHmm")}')
	run(f'rm -f {" ".join(obs_files)}')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Convert GDAS to LITTLE_R.\n\nLongrun Weather Inc., NWP operation software.\nCopyright (C) 2018-2019 All Rights Reserved.", formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('-t', '--time', help='Convert GDAS data at date time (YYYYMMDDHH).', type=parse_time)
	parser.add_argument('-i', '--gdas-root', dest='gdas_root', help='Root directory to store GDAS data.')
	parser.add_argument('-o', '--littler-root', dest='littler_root', help='Root directory to store output LITTLE_R data.')
	parser.add_argument('-v', '--verbose', help='Print out build log', action='store_true')
	parser.add_argument('-f', '--force', help='Force to run', action='store_true')
	args = parser.parse_args()

	if not args.gdas_root:
		if os.getenv('RAWDATA_ROOT'):
			args.gdas_root = os.getenv('RAWDATA_ROOT') + '/gdas'
		else:
			cli.error('Option --gdas-root or environment variable RAWDATA_ROOT need to be set!')
	args.gdas_root = os.path.abspath(args.gdas_root)
	if not os.path.isdir(args.gdas_root):
		cli.error(f'Directory {args.gdas_root} does not exist!')

	if not args.littler_root:
		if os.getenv('RAWDATA_ROOT'):
			args.littler_root = os.getenv('RAWDATA_ROOT') + '/littler'
		else:
			cli.error('Option --littler-root or environment variable RAWDATA_ROOT need to be set!')
	args.littler_root = os.path.abspath(args.littler_root)
	if not os.path.isdir(args.littler_root):
		cli.error(f'Directory {args.littler_root} does not exist!')


	convert_gdas(args.gdas_root, args.littler_root, args.time, args)
