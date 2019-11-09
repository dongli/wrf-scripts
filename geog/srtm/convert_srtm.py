#!/usr/bin/env python3

from argparse import ArgumentParser
from osgeo import gdal
import os
import sys
script_root = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_root)

# Use WPS write_geogrid.c to write specified binary data format.
try:
	import write_geogrid
except:
	owd = os.getcwd()
	os.chdir(script_root)
	os.system(f'{sys.executable} setup.py build_ext --inplace')
	os.system(f'rm -rf build write_geogrid.c')
	import write_geogrid
	os.chdir(owd)

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt

parser = ArgumentParser('Convert SRTM tiles to WPS compatible files.')
parser.add_argument('--srtm-dir', dest='srtm_dir', help='Directory of SRTM ZIP files')
parser.add_argument('--srtm-tif', dest='srtm_tif', help='Single SRTM TIFF file')
args = parser.parse_args()

if args.srtm_dir:
	for zip_file_name in glob(f'{args.srtm_dir}/srtm_*.zip'):
		file_prefix = zip_file_name.replace('.zip', '')
		if not os.path.isfile(file_prefix + '.tif'):
			cli.blue_arrow('Decompressing {zip_file_name} ...')
			run(f'unzip {zip_file_name}')
		cli.blue_arrow(f'Read {file_prefix} ...')
		tile = gdal.Open(file_prefix + '.tif')
		num_lon = tile.RasterXSize
		num_lat = tile.RasterYSize
		gt = tile.GetGeoTransform()
		min_lon = gt[0]
		min_lat = gt[3] + num_lon * gt[4] + num_lat * gt[5]
		max_lon = gt[0] + num_lon * gt[1] + num_lat * gt[2]
		max_lat = gt[3]
		topo = tile.ReadAsArray()
elif args.srtm_tif:
	tile = gdal.Open(args.srtm_tif)
	num_lon = tile.RasterXSize
	num_lat = tile.RasterYSize
	topo = tile.ReadAsArray()
	write_geogrid.write_2d_array(topo.astype('float32'))
