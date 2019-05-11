import fileinput
import re

def edit_file(filepath, changes, return_on_first_match=False):
	try:
		matched = False
		with fileinput.FileInput(filepath, inplace=True) as file:
			for line in file:
				changed_line = line
				if not return_on_first_match or not matched:
					for change in changes:
						if re.search(change[0], changed_line, flags=re.IGNORECASE):
							changed_line = re.sub(change[0], change[1], changed_line, flags=re.IGNORECASE)
							matched = True
				print(changed_line, end='')
	except Exception as e:
		print('[Error]: Failed to edit file {}! {}'.format(filepath, e))
		exit(1)
