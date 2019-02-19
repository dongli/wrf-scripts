import cli
import re
import os
from packaging.version import Version, parse

def wrf_version(wrf_root):
	if os.path.isfile(f'{wrf_root}/README'):
		line = open(f'{wrf_root}/README', 'r').readline()
	elif os.path.isfile(f'{wrf_root}/README.WRFPLUS'):
		line = open(f'{wrf_root}/README.WRFPLUS', 'r').readlines()[1]
	else:
		cli.error('Could not find WRF version!')
	match = re.search('Version (\d+\.\d+(\.\d+)?)', line)[1]
	return parse(match)
