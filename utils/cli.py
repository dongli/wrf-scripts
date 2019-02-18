import sys

color_map = {
	'red': 31,
	'green': 32,
	'yellow': 33,
	'blue': 34,
	'purple': 35,
	'cyan': 36,
	'gray': 37,
	'white': 39
}

def escape(n):
	if sys.stdout.isatty():
		return f'\033[{n}m'
	else:
		return ''

def reset():
	return escape(0)

def color(n):
	return escape(f'0;{n}')

def bold(message):
	return f'{escape(1)}{message}{escape(0)}'

for name, code in color_map.items():
	exec(f'''
def {name}(message=None):
	if message != None:
		return {name}() + message + reset()
	else:
		return color({color_map[name]})
	''')

def notice(message):
	print(f'[{green("Notice")}]: {message}')

def warning(message):
	print(f'[{yellow("Warning")}]: {message}')

def error(message):
	print(f'[{red("Error")}]: {message}')
	exit(1)

def banner(message):
	print()
	print('===================================================================================')
	print(message)
	print()
