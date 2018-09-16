import cli
import os

def check_files(expected_files, fatal=False):
	result = True
	for file in expected_files:
		if not os.path.isfile(file):
			if fatal: cli.error(f'File {exe} has not been generated!')
			result = False
			break
	return result

