import cli
import json
import os
import pendulum

def parse_config(config_json):
	config = {}

	if os.path.isfile(config_json):
		config = json.loads(open(config_json, 'r').read())
	else:
		try:
			config = json.loads(config_json)
		except:
			cli.error(f'{cli.red(config_json)} is not a JSON file or text!')

	# Set defaults.
	if not 'share' in config: config['share'] = {}
	if not 'domains' in config: config['domains'] = {}
	if not 'max_dom' in config['share'] and 'max_dom' in config['domains']:
		config['share']['max_dom'] = config['domains']['max_dom']
	elif not 'max_dom' in config['domains'] and 'max_dom' in config['share']:
		config['domains']['max_dom'] = config['share']['max_dom']
	elif 'max_dom' in config['share'] and 'max_dom' in config['domains']:
		if config['share']['max_dom'] != config['domains']['max_dom']:
			cli.error(f'Parameter max_dom is not consistent in {config_json}!')
	else:
		config['share']['max_dom'] = 1
		config['domains']['max_dom'] = 1
	if config['domains']['max_dom'] == 1 and not 'parent_grid_ratio' in config['domains']:
		config['domains']['parent_grid_ratio'] = [1]
		config['domains']['i_parent_start'] = [1]
		config['domains']['j_parent_start'] = [1]
	if not 'parent_time_step_ratio' in config['domains']:
		config['domains']['parent_time_step_ratio'] = config['domains']['parent_grid_ratio']
	config['domains']['grid_id'] = [i + 1 for i in range(config['domains']['max_dom'])]

	# Transform parameters.
	config['custom']['start_time'] = pendulum.from_format(config['custom']['start_time'], 'YYYYMMDDHH')
	if not 'end_time' in config['custom']:
		config['custom']['end_time'] = config['custom']['start_time'].add(hours=config['custom']['forecast_hours'])
	else:
		config['custom']['end_time'] = pendulum.from_format(config['custom']['end_time'], 'YYYYMMDDHH')
	if not type(config['geogrid']['dx']) == list: config['geogrid']['dx'] = [config['geogrid']['dx']]
	if not type(config['geogrid']['dy']) == list: config['geogrid']['dy'] = [config['geogrid']['dy']]

	for key in ('e_we', 'e_sn', 'dx', 'dy'):
		config['domains'][key] = config['geogrid'][key]

	# Set time step if not set yet.
	if not 'time_step' in config['domains']:
		if config['geogrid']['dx'][0] >= 30000:
 			config['domains']['time_step'] = 120
		elif 25000 <= config['geogrid']['dx'][0] < 30000:
			config['domains']['time_step'] = 120
		elif 20000 <= config['geogrid']['dx'][0] < 25000:
			config['domains']['time_step'] = 120
		elif 15000 <= config['geogrid']['dx'][0] < 20000:
			config['domains']['time_step'] = 90
		elif 10000 <= config['geogrid']['dx'][0] < 15000:
			config['domains']['time_step'] = 60
		elif 5000 <= config['geogrid']['dx'][0] < 10000:
			config['domains']['time_step'] = 30
		elif 2500 <= config['geogrid']['dx'][0] >= 5000:
			config['domains']['time_step'] = 10
		else:
			config['domains']['time_step'] = 5

	if not 'ob_format' in config['wrfda']:
		config['wrfda']['ob_format'] = 2
	if config['wrfda']['ob_format'] == 1 and not 'prepbufr_source' in config['wrfda']:
		config['wrfda']['prepbufr_source'] = 'gdas'

	return config
