from glob import glob
import re

def search_files(file_paths, pattern):
	for file_path in glob(file_paths):
		f = open(file_path, 'r')
		try:
			if re.search(pattern, f.readlines(), re.MULTILINE):
				return True
		except:
			return False
	return False
