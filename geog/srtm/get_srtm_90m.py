#!/usr/bin/env python3

from argparse import ArgumentParser
import requests
from bs4 import BeautifulSoup
import os
import re
import signal
import sys

parser = ArgumentParser('Get SRTM tiles from official site.')
parser.add_argument('-o', '--output-dir', dest='output_dir', help='Directory to store SRTM ZIP files', required=True)
parser.add_argument('-t', '--type', help='SRTM data type', choices=('geotiff', 'ascii'), default='geotiff')
parser.add_argument('--tile', help='Download a specific tile')
args = parser.parse_args()

if args.type == 'geotiff':
	url = 'http://data.cgiar-csi.org/srtm/tiles/GeoTIFF/'
elif args.type == 'ascii':
	url = 'http://data.cgiar-csi.org/srtm/tiles/ASCII/'

def signal_handler(sig, frame):
	sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)

if not os.path.isdir(args.output_dir):
	os.makedirs(args.output_dir)
os.chdir(args.output_dir)

def download(tile):
	if not os.path.isfile(tile):
		print(f'==> Downloading {tile} ...')
		while True:
			try:
				content = requests.get(f'{url}/{tile}', auth=('data_public', 'GDdci'), timeout=120).content
				break
			except requests.exceptions.RequestException as e:
				print(f'--> Failed due to {e}, retry!')
				pass
		open(tile, 'wb').write(content)

if args.tile:
	download(args.tile)
else:
	page = requests.get(url, auth=('data_public', 'GDdci')).text
	soup = BeautifulSoup(page, 'lxml')
	for item in soup.find_all('a'):
		if re.search('^srtm', item['href']):
			download(item['href'])
