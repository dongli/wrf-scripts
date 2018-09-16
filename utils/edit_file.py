import fileinput
import re

def edit_file(filepath, changes):
	try:
		with fileinput.FileInput(filepath, inplace=True) as file:
			for line in file:
				found = False
				for change in changes:
					if re.search(change[0], line, flags=re.IGNORECASE):
						print(re.sub(change[0], change[1], line, flags=re.IGNORECASE), end='')
						found = True
						break
				if not found:
					print(line, end='')
	except Exception as e:
		print('[Error]: Failed to edit file {}! {}'.format(filepath, e))
		exit(1)
