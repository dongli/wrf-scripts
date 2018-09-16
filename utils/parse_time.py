import pendulum
import re

def parse_time(string):
	match = re.match(r'(\d{4}\d{2}\d{2}\d{2})(\d{2})?', string)
	if match.group(2):
		return pendulum.from_format(string, '%Y%m%d%H%M')
	else:
		return pendulum.from_format(string, '%Y%m%d%H')

