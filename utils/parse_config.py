import cli
import json
import os
import pendulum
from dict_helpers import has_key

def check_mandatory_params(config, keys):
	for key in keys:
		if not key in config:
			cli.error(f'Parameter {key} is not in configuration file!')

def change_to_array(config, keys):
	if not has_key(config, keys): return
	if len(keys) == 1:
		if type(config[keys[0]]) != list:
			config[keys[0]] = [config[keys[0]]]
	elif len(keys) == 2:
		if type(config[keys[0]][keys[1]]) != list:
			config[keys[0]][keys[1]] = [config[keys[0]][keys[1]]]
	elif len(keys) == 3:
		if type(config[keys[0]][keys[1]][keys[2]]) != list:
			config[keys[0]][keys[1]][keys[2]] = [config[keys[0]][keys[1]][keys[2]]]

def check_array_size(config, keys, size):
	if not has_key(config, keys): return
	if len(keys) == 1:
		if len(config[keys[0]]) != size:
			cli.error(f'Parameter max_dom is {config["domains"]["max_dom"]}, but {keys} only has {len(config[keys[0]])} elements!')
	elif len(keys) == 2:
		if len(config[keys[0]][keys[1]]) != size:
			cli.error(f'Parameter max_dom is {config["domains"]["max_dom"]}, but {keys} only has {len(config[keys[0]][keys[1]])} elements!')
	elif len(keys) == 3:
		if len(config[keys[0]][keys[1]][keys[2]]) != size:
			cli.error(f'Parameter max_dom is {config["domains"]["max_dom"]}, but {keys} only has {len(config[keys[0]][keys[1]][keys[2]])} elements!')

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
	if not has_key(config, 'share'): config['share'] = {}
	if not has_key(config, 'domains'): config['domains'] = {}
	check_mandatory_params(config['domains'], ('max_dom', 'dx', 'dy', 'e_we', 'e_sn'))
	# - parent_grid_ratio, parent_time_step_ratio, i_parent_start, j_parent_start
	if config['domains']['max_dom'] == 1:
		config['domains']['parent_grid_ratio'] = [1]
		config['domains']['parent_time_step_ratio'] = [1]
		config['domains']['i_parent_start'] = [1]
		config['domains']['j_parent_start'] = [1]
	else:
		if has_key(config, ('custom', 'start_time')):
			check_mandatory_params(config['domains'], ['parent_time_step_ratio'])
		check_mandatory_params(config['domains'], ('i_parent_start', 'j_parent_start'))
	# Change to array.
	change_to_array(config, ('domains', 'dx'                    ))
	change_to_array(config, ('domains', 'dy'                    ))
	change_to_array(config, ('domains', 'e_we'                  ))
	change_to_array(config, ('domains', 'e_sn'                  ))
	change_to_array(config, ('domains', 'e_vert'                ))
	change_to_array(config, ('domains', 'parent_time_step_ratio'))
	change_to_array(config, ('domains', 'i_parent_start'        ))
	change_to_array(config, ('domains', 'j_parent_start'        ))
	# Check dimension.
	check_array_size(config, ('domains', 'dx'                    ), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'dy'                    ), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'e_we'                  ), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'e_sn'                  ), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'e_vert'                ), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'parent_time_step_ratio'), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'i_parent_start'        ), config['domains']['max_dom'])
	check_array_size(config, ('domains', 'j_parent_start'        ), config['domains']['max_dom'])
	if not has_key(config, ('domains', 'parent_grid_ratio')):
		config['domains']['parent_grid_ratio'] = [1]
		for i in range(1, len(config['domains']['dx'])):
			config['domains']['parent_grid_ratio'].append(int(config['domains']['dx'][i-1] / config['domains']['dx'][i]))
	config['domains']['grid_id'] = [i + 1 for i in range(config['domains']['max_dom'])]
	if not has_key(config, ('domains', 'parent_id')):
		config['domains']['parent_id'] = [i for i in range(config['domains']['max_dom'])]

	# Transform parameters.
	if has_key(config, ('custom', 'start_time')):
		config['custom']['start_time'] = pendulum.from_format(config['custom']['start_time'], 'YYYYMMDDHH')
		if not has_key(config, ('custom', 'end_time')):
			config['custom']['end_time'] = config['custom']['start_time'].add(hours=config['custom']['forecast_hours'])
		else:
			config['custom']['end_time'] = pendulum.from_format(config['custom']['end_time'], 'YYYYMMDDHH')
	if not type(config['domains']['dx']) == list: config['domains']['dx'] = [config['domains']['dx']]
	if not type(config['domains']['dy']) == list: config['domains']['dy'] = [config['domains']['dy']]

	for key in ('e_we', 'e_sn', 'parent_id', 'parent_grid_ratio', 'i_parent_start', 'j_parent_start'):
		config['geogrid'][key] = config['domains'][key]
	config['geogrid']['dx'] = config['domains']['dx'][0]
	config['geogrid']['dy'] = config['domains']['dy'][0]

	# Set time step if not set yet.
	if not has_key(config, ('domains', 'time_step')):
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

	if not has_key(config, 'time_control'): config['time_control'] = {}

	# wrfvar* sections
	for tag in range(1, 23):
		section = f'wrfvar{tag}'
		if not section in config: config[section] = {}
	if not has_key(config, ('wrfvar3', 'ob_format')):
		config['wrfvar3']['ob_format'] = 2
	if config['wrfvar3']['ob_format'] == 1 and not has_key(config, ('custom', 'da', 'prepbufr_source')):
		config['custom']['da']['prepbufr_source'] = 'gdas'

	return config
