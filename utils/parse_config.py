import cli
import json
import os
import pendulum

def parse_domain(config):
	if 'min_lat' in config:
		config['ref_lat'] = 0.5 * (config['min_lat'] + config['max_lat'])
		config['ref_lon'] = 0.5 * (config['min_lon'] + config['max_lon'])
	if not 'stand_lon' in config:
		config['stand_lon'] = config['ref_lon']
	if not 'truelat1' in config:
		config['truelat1'] = 30.0
		config['truelat2'] = 60.0

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
