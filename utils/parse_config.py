import cli
import json
import os
import pendulum
import numpy as np
import decimal
from math import cos, sin, asin, sqrt
from pprint import pprint

EARTH_RADIUS = 6378388

def round_grid_number(number):
	# 134 -> 130
	# 139 -> 140
	# 145 -> 140
	return int(decimal.Decimal(number * 0.01).quantize(decimal.Decimal('0.1')) * 100)

def parse_domain(config):
	if config['max_dom'] > 1 and not 'parent_grid_ratio' in config:
		cli.error('parent_grid_ratio is needed in config file!')

	if 'min_lon' in config and type(config['min_lon']) != list: config['min_lon'] = [config['min_lon']]
	if 'max_lon' in config and type(config['max_lon']) != list: config['max_lon'] = [config['max_lon']]
	if 'min_lat' in config and type(config['min_lat']) != list: config['min_lat'] = [config['min_lat']]
	if 'max_lat' in config and type(config['max_lat']) != list: config['max_lat'] = [config['max_lat']]

	config['min_lon'] = np.array(config['min_lon'])
	config['max_lon'] = np.array(config['max_lon'])
	config['min_lat'] = np.array(config['min_lat'])
	config['max_lat'] = np.array(config['max_lat'])

	if 'min_lat' in config:
		config['ref_lat'] = 0.5 * (config['min_lat'][0] + config['max_lat'][0])
		config['ref_lon'] = 0.5 * (config['min_lon'][0] + config['max_lon'][0])
	if not 'stand_lon' in config:
		config['stand_lon'] = config['ref_lon']
	if not 'truelat1' in config:
		config['truelat1'] = 30.0
		config['truelat2'] = 60.0

	# Calculate grid numbers.
	min_lon = np.radians(config['min_lon'])
	max_lon = np.radians(config['max_lon'])
	min_lat = np.radians(config['min_lat'])
	max_lat = np.radians(config['max_lat'])
	# TODO: Handle edge cases.
	lon_span = max_lon - min_lon
	lat_span = max_lat - min_lat
	dx = config['resolution']
	dy = config['resolution']
	config['e_we'] = [round_grid_number(EARTH_RADIUS * cos(np.radians(config['ref_lat'])) * lon_span[0] / dx)]
	config['e_sn'] = [round_grid_number(EARTH_RADIUS * lat_span[0] / dy)]

	# For nested domains.
	for i in range(1, config['max_dom']):
		grid_ratio = config['parent_grid_ratio'][i]
		dx = config['resolution'] / grid_ratio
		dy = config['resolution'] / grid_ratio
		lat = min_lat[i] + lat_span[i] / 2
		n = round_grid_number(EARTH_RADIUS * cos(lat) * lon_span[i] / dx)
		config['e_we'].append(int(n / grid_ratio) * grid_ratio + 1)
		n = round_grid_number(EARTH_RADIUS * lat_span[i] / dy)
		config['e_sn'].append(int(n / grid_ratio) * grid_ratio + 1)

def parse_config(config_json):
	config = {}

	if os.path.isfile(config_json):
		config = json.loads(open(config_json, 'r').read())
	else:
		try:
			config = json.loads(config_json)
		except:
			cli.error(f'{cli.red(config_json)} is not a JSON file or text!')

	common_config = config['common']
	# Set defaults.
	if not 'max_dom' in common_config: common_config['max_dom'] = 1

	# Transform parameters.
	common_config['start_time'] = pendulum.from_format(common_config['start_time'], 'YYYYMMDDHH')
	common_config['end_time'] = common_config['start_time'].add(hours=common_config['forecast_hour'])
	parse_domain(common_config)

	return config
