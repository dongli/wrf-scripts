import cli
import os
import psutil
import subprocess

def check_files(expected_files, fatal=False):
	result = True
	if type(expected_files) == str:
		expected_files = [expected_files]
	for file in expected_files:
		if not os.path.isfile(file):
			if fatal: cli.error(f'File {file} has not been generated!')
			result = False
			break
	return result

def check_file_size(url, local_file_path):
	res = subprocess.run(['curl', '-I', url], stdout=subprocess.PIPE)
	return f'Content-Length: {os.path.getsize(local_file_path)}' in res.stdout.decode('utf-8')

def is_downloading(local_file_path):
	for pid in psutil.pids():
		p = psutil.Process(pid)
		if local_file_path in p.cmdline():
			return True
		else:
			return False
