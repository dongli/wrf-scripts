from glob import glob
import re

def search_files(file_paths, pattern):
	for file_path in glob(file_paths):
		f = open(file_path, 'r')
		if re.search(pattern, f.readlines(), re.MULTILINE):
			return True
	return False
