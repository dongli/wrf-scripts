import cli
import os
import subprocess

def run(cmd, bg=False):
	print(f'{cli.blue("==>")} {cmd}')
	if bg:
		return subprocess.Popen(cmd.split())
	else:
		os.system(cmd)
