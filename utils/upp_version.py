import cli
import re
import os
from packaging.version import Version, parse

def upp_version(upp_root):
	if os.path.isfile(f'{upp_root}/arch/version'):
		line = open(f'{upp_root}/arch/version', 'r').readline()
	elif os.path.isfile(f'{upp_root}/version'):
		line = open(f'{upp_root}/version', 'r').readline()
	else:
		cli.error('Could not find UPP version!')
	match = re.search('UPPV(\d+\.\d+(\.\d+)?)', line)[1]
	return parse(match)
