import cli
import re
import os
from packaging.version import Version, parse

def upp_version(upp_root):
	if os.path.isfile(f'{upp_root}/arch/version'):
		line = open(f'{upp_root}/arch/version', 'r').readline()
		match = re.search('UPPV(\d+\.\d+(\.\d+)?)', line)[1]
	elif os.path.isfile(f'{upp_root}/version'):
		line = open(f'{upp_root}/version', 'r').readline()
		match = re.search('(\d+\.\d+(\.\d+)?)', line)[1]
	else:
		cli.error('Could not find UPP version!')
	return parse(match)
