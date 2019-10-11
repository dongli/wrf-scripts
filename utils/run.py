import cli
import os
import subprocess

def run(cmd, bg=False, raise_error=False, stdout=False, echo=True):
	if echo: print(f'{cli.blue("==>")} {cmd}')
	if bg:
		return subprocess.Popen(cmd.split())
	elif raise_error or stdout:
		res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if raise_error:
			try:
				res.check_returncode()
			except:
				print(res.stdout.decode('utf-8'))
				raise
		if stdout: return res.stdout.decode('utf-8').strip()
	else:
		os.system(cmd)
