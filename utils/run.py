import cli
import os

def run(cmd):
	print(f'{cli.blue("==>")} {cmd}')
	os.system(cmd)
