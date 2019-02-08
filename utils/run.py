import cli
import os
import subprocess

def run(cmd, bg=False, raise_error=False):
	print(f'{cli.blue("==>")} {cmd}')
	if bg:
		return subprocess.Popen(cmd.split())
	elif raise_error:
		res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
		if raise_error:
			try:
				res.check_returncode()
			except:
				print(res.stdout.decode('utf-8'))
				raise
	else:
		os.system(cmd)
