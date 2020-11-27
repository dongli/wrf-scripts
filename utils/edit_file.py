import fileinput
import re
import cli

def edit_file(filepath, changes, return_on_first_match=False):
	try:
		matched = False
		with fileinput.FileInput(filepath, inplace=True) as file:
			line_number = 1
			for line in file:
				changed_line = line
				if not return_on_first_match or not matched:
					for change in changes:
						if type(change[0]) == int:
							if line_number == change[0]: changed_line = change[1]
						elif re.search(change[0], changed_line, flags=re.IGNORECASE):
							changed_line = re.sub(change[0], change[1], changed_line, flags=re.IGNORECASE)
							matched = True
				print(changed_line, end='')
				line_number += 1
	except Exception as e:
		cli.error(f'Failed to edit file {filepath}! {e}')
