import cli
import json
import os
import pendulum

def check_mandatory_params(config, keys):
	for key in keys:
		if not key in config:
			cli.error(f'Parameter {key} is not in configuration file!')

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
	check_mandatory_params(config['domains'], ('max_dom', 'dx', 'dy', 'e_we', 'e_sn', 'e_vert'))
	# - parent_grid_ratio, parent_time_step_ratio, i_parent_start, j_parent_start, parent_id
	if config['domains']['max_dom'] == 1:
		config['domains']['parent_grid_ratio'] = [1]
		config['domains']['parent_time_step_ratio'] = [1]
		config['domains']['i_parent_start'] = [1]
		config['domains']['j_parent_start'] = [1]
	else:
		check_mandatory_params(config['domains'], ('parent_time_step_ratio', 'i_parent_start', 'j_parent_start'))
	# Change to array.
	for key in ('dx', 'dy', 'e_we', 'e_sn', 'e_vert', 'parent_time_step_ratio', 'i_parent_start', 'j_parent_start'):
		if type(config['domains'][key]) != list:
			config['domains'][key] = [config['domains'][key]]
	if not 'parent_grid_ratio' in config['domains']:
		config['domains']['parent_grid_ratio'] = [1]
		for i in range(1, len(config['domains']['dx'])):
			config['domains']['parent_grid_ratio'].append(int(config['domains']['dx'][i-1] / config['domains']['dx'][i]))
	config['domains']['grid_id'] = [i + 1 for i in range(config['domains']['max_dom'])]
	config['domains']['parent_id'] = [i for i in range(config['domains']['max_dom'])]

	# Transform parameters.
	config['custom']['start_time'] = pendulum.from_format(config['custom']['start_time'], 'YYYYMMDDHH')
	if not 'end_time' in config['custom']:
		config['custom']['end_time'] = config['custom']['start_time'].add(hours=config['custom']['forecast_hours'])
	else:
		config['custom']['end_time'] = pendulum.from_format(config['custom']['end_time'], 'YYYYMMDDHH')
	if not type(config['domains']['dx']) == list: config['domains']['dx'] = [config['domains']['dx']]
	if not type(config['domains']['dy']) == list: config['domains']['dy'] = [config['domains']['dy']]

	for key in ('e_we', 'e_sn', 'parent_grid_ratio', 'i_parent_start', 'j_parent_start'):
		config['geogrid'][key] = config['domains'][key]
	config['geogrid']['dx'] = config['domains']['dx'][0]
	config['geogrid']['dy'] = config['domains']['dy'][0]

	# Set time step if not set yet.
	if not 'time_step' in config['domains']:
		if config['domains']['dx'][0] >= 30000:
 			config['domains']['time_step'] = 120
		elif 25000 <= config['domains']['dx'][0] < 30000:
			config['domains']['time_step'] = 120
		elif 20000 <= config['domains']['dx'][0] < 25000:
			config['domains']['time_step'] = 120
		elif 15000 <= config['domains']['dx'][0] < 20000:
			config['domains']['time_step'] = 90
		elif 10000 <= config['domains']['dx'][0] < 15000:
			config['domains']['time_step'] = 60
		elif 5000 <= config['domains']['dx'][0] < 10000:
			config['domains']['time_step'] = 30
		elif 2500 <= config['domains']['dx'][0] >= 5000:
			config['domains']['time_step'] = 10
		else:
			config['domains']['time_step'] = 5

	if not 'ob_format' in config['wrfda']:
		config['wrfda']['ob_format'] = 2
	if config['wrfda']['ob_format'] == 1 and not 'prepbufr_source' in config['wrfda']:
		config['wrfda']['prepbufr_source'] = 'gdas'

	return config
