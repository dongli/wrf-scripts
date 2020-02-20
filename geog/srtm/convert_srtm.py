#!/usr/bin/env python3

from argparse import ArgumentParser
from osgeo import gdal
import numpy as np
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
	os.system(f'{sys.executable} setup.py build_ext --inplace --include-dirs={np.get_include()}')
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

def geo_name(srtm_tif):
	i = int(srtm_tif[5:7])
	j = int(srtm_tif[8:10])
	is_ew = (i - 1) * 6000 + 1
	ie_ew = is_ew + 6000 - 1
	js_sn = (24 - j) * 6000 + 1
	je_sn = js_sn + 6000 - 1
	return '{:06}-{:06}.{:06}-{:06}'.format(is_ew, ie_ew, js_sn, je_sn)

def write(topo):
	topo[topo == -32768] = -9999
	topo = np.flip(topo, axis=0)
	write_geogrid.write_2d_array(topo.astype('float32'))
	os.system(f'mv 00001-06000.00001-06000 {geo_name(args.srtm_tif)}')

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
		write(topo)
elif args.srtm_tif:
	tile = gdal.Open(args.srtm_tif)
	num_lon = tile.RasterXSize
	num_lat = tile.RasterYSize
	topo = tile.ReadAsArray()
	write(topo)
