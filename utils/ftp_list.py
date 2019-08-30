import ftplib
import os
import re

def ftp_list(ftp, file_path_pattern, connect):
	remote_dir = os.path.dirname(file_path_pattern)
	pattern = os.path.basename(file_path_pattern)
	try:
		res = []
		for file_name in ftp.nlst(remote_dir):
			if re.search(pattern, file_name):
				res.append(remote_dir + '/' + os.path.basename(file_name))
		return res
	except ftplib.all_errors as e:
		if type(e.args[0]) == str and e.args[0][:3] == '550':
			return []
		else:
			ftp = connect()
			return ftp_list(ftp, file_path_pattern, connect)
	return []
