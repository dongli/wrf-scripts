import cli
import json
import os
import pendulum
import numpy as np
import decimal
from math import cos, sin, asin, sqrt
from pyproj import *

EARTH_RADIUS = 6378388

def round_grid_number(number):
	# 134 -> 130
	# 139 -> 140
	# 145 -> 140
	return int(decimal.Decimal(number * 0.01).quantize(decimal.Decimal('0.1')) * 100)

def parse_domain(config):
	if config['max_dom'] > 1 and not 'parent_grid_ratio' in config:
		cli.error('parent_grid_ratio is needed in config file!')

	# Coarse domain
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

	# Create proj object.
	p = Proj('+proj=lcc +lon_0=105.0 +lat_0=32.5 +lat_1=30.0 +lat_2=60.0')
	proj = Proj(f'''
		+proj=lcc
		+lon_0={config["ref_lon"]}
		+lat_0={config["ref_lat"]}
		+lat_1={config["truelat1"]}
		+lat_2={config["truelat2"]}
	''')

	# Calculate grid numbers.
	# For coarse domain
	dx = [config['resolution']]
	dy = [config['resolution']]
	min_lon = config['min_lon'][0]
	max_lon = config['max_lon'][0]
	min_lat = config['min_lat'][0]
	max_lat = config['max_lat'][0]
	west_middle  = proj(min_lon, (min_lat + max_lat) * 0.5)
	east_middle  = proj(max_lon, (min_lat + max_lat) * 0.5)
	south_middle = proj((min_lon + max_lon) * 0.5, min_lat)
	north_middle = proj((min_lon + max_lon) * 0.5, max_lat)
	# TODO: Handle edge cases.
	x_span = east_middle[0] - west_middle[0]
	y_span = north_middle[1] - south_middle[1]
	config['e_we'] = [round_grid_number(x_span / dx[0])]
	config['e_sn'] = [round_grid_number(y_span / dy[0])]
	config['i_parent_start'] = [1]
	config['j_parent_start'] = [1]
	config['_west_south_x'] = [-x_span * 0.5]
	config['_west_south_y'] = [-y_span * 0.5]

	# For nested domains
	for i in range(1, config['max_dom']):
		parent_id = config['parent_id'][i] - 1
		grid_ratio = config['parent_grid_ratio'][i]
		dx.append(dx[parent_id] / grid_ratio)
		dy.append(dy[parent_id] / grid_ratio)
		nest_min_lon = config['min_lon'][i]
		nest_max_lon = config['max_lon'][i]
		nest_min_lat = config['min_lat'][i]
		nest_max_lat = config['max_lat'][i]
		nest_west_middle  = proj(nest_min_lon, (nest_min_lat + nest_max_lat) * 0.5)
		nest_east_middle  = proj(nest_max_lon, (nest_min_lat + nest_max_lat) * 0.5)
		nest_south_middle = proj((nest_min_lon + nest_max_lon) * 0.5, nest_min_lat)
		nest_north_middle = proj((nest_min_lon + nest_max_lon) * 0.5, nest_max_lat)
		nest_x_span = nest_east_middle[0] - nest_west_middle[0]
		nest_y_span = nest_north_middle[1] - nest_south_middle[1]
		n = round_grid_number(nest_x_span / dx[i])
		config['e_we'].append(int(n / grid_ratio) * grid_ratio + 1)
		n = round_grid_number(nest_y_span / dy[i])
		config['e_sn'].append(int(n / grid_ratio) * grid_ratio + 1)
		nest_ref_x, nest_ref_y = proj((nest_min_lon + nest_max_lon) * 0.5, (nest_min_lat + nest_max_lat) * 0.5)
		config['_west_south_x'].append(nest_ref_x - nest_x_span * 0.5)
		config['_west_south_y'].append(nest_ref_y - nest_y_span * 0.5)
		config['i_parent_start'].append(int((config['_west_south_x'][i] - config['_west_south_x'][parent_id]) / dx[parent_id]))
		config['j_parent_start'].append(int((config['_west_south_y'][i] - config['_west_south_y'][parent_id]) / dy[parent_id]))

	# Clean internal data.
	config.pop('_west_south_x')
	config.pop('_west_south_y')

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
	common_config['end_time'] = common_config['start_time'].add(hours=common_config['forecast_hours'])
	parse_domain(common_config)
	# Set time step if not set yet.
	if not 'time_step' in common_config:
		if common_config['resolution'] >= 30000:
 			common_config['time_step'] = 120
		elif 25000 <= common_config['resolution'] < 30000:
			common_config['time_step'] = 90
		elif 20000 <= common_config['resolution'] < 15000:
			common_config['time_step'] = 60
		elif 15000 <= common_config['resolution'] < 20000:
			common_config['time_step'] = 30
		elif 10000 <= common_config['resolution'] < 15000:
			common_config['time_step'] = 30
		elif 5000 <= common_config['resolution'] < 10000:
			common_config['time_step'] = 10
		elif 2500 <= common_config['resolution'] >= 5000:
			common_config['time_step'] = 10
		else:
			common_config['time_step'] = 5

	return config
