import ftplib
import os
import re

def ftp_exist(ftp, file_path_pattern, connect):
	remote_dir = os.path.dirname(file_path_pattern)
	pattern = os.path.basename(file_path_pattern)
	try:
		for file_name in ftp.nlst(remote_dir):
			if re.search(pattern, file_name):
				return remote_dir + '/' + os.path.basename(file_name)
	except ftplib.all_errors as e:
		if e.args[0][:3] == '550':
			return False
		else:
			ftp = connect()
			return ftp_exist(ftp, file_path_pattern, connect)
	return False
