import argparse
import pendulum
import re

def parse_time(string):
	match = re.match(r'(\d{4}\d{2}\d{2}\d{2})(\d{2})?', string)
	if match.group(2):
		return pendulum.from_format(string, 'YYYYMMDDHHmm')
	else:
		return pendulum.from_format(string, 'YYYYMMDDHH')

def parse_time_range(string):
	match = re.match(r'(\d{4}\d{2}\d{2}\d{2}(\d{2}))-(\d{4}\d{2}\d{2}\d{2}(\d{2}))', string)
	if not match:
		raise argparse.ArgumentError('"' + string + '" is not a time range (YYYYMMDDHH-YYYYMMDDHH)!')
	if len(match.groups()) == 2:
		return (pendulum.from_format(match.group(1), 'YYYYMMDDHH'), pendulum.from_format(match.group(2), 'YYYYMMDDHH'))
	elif len(match.groups()) == 4:
		return (pendulum.from_format(match.group(1), 'YYYYMMDDHHmm'), pendulum.from_format(match.group(3), 'YYYYMMDDHHmm'))

def parse_forecast_hours(string):
	match = re.match(r'(\d+)-(\d+)\+(\d+)', string)
	if match:
		start = int(match.group(1))
		end = int(match.group(2))
		step = int(match.group(3))
		return [x for x in range(start, end + step, step)]
	match = re.findall(r'(\d+):?', string)
	if match:
		return [int(match[i]) for i in range(len(match))]
