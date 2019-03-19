import cli
import re
import os
from packaging.version import Version, parse

def gsi_version(gsi_root):
	if os.path.isfile(f'{gsi_root}/README.comgsi'):
		f = open(f'{gsi_root}/README.comgsi', 'r')
		f.readline()
		line = f.readline()
	else:
		cli.warning('Could not find GSI version! Assume 3.6.')
		return parse('3.6')
	# Community GSIv3.7_EnKFv1.3
	match = re.search('GSIv(\d+\.\d+)', line)[1]
	return parse(match)
