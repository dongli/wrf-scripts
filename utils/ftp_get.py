import ftplib
import os
import threading

def ftp_get(ftp, remote_file_path, local_dir, connect, thread_size=0, force=False, fatal=True):
	# Ensure connection is good.
	ftp = connect()
	if not os.path.isdir(local_dir): os.makedirs(local_dir)
	local_file_path = local_dir + '/' + os.path.basename(remote_file_path)
	try:
		remote_size = ftp.size(remote_file_path)
		if os.path.isfile(local_file_path):
			local_size = os.path.getsize(local_file_path)
			if remote_size == local_size:
				print(f'[Warning]: File {local_file_path} exists!')
				return
			# Redownload from start!
			if force:
				os.remove(local_file_path)
			else:
				print(f'[Error]: File {local_file_path} exists, but is not complete!')
				if fatal: exit(1)
		if thread_size > 0:
			block_size = int(remote_size / thread_size - 1)
			last_block_size = block_size + int(remote_size - block_size * thread_size)
			print(f'[Notice]: Download in {thread_size} threads.')
			threads = []
			for i in range(thread_size - 1):
				begin_pos = block_size * i
				thread = threading.Thread(target=ftp_get_thread, args=(i, remote_file_path, local_file_path, connect, force, fatal, begin_pos, block_size))
				threads.append(thread)
			begin_pos = block_size * (thread_size - 1)
			thread = threading.Thread(target=ftp_get_thread, args=(thread_size - 1, remote_file_path, local_file_path, connect, force, fatal, begin_pos, last_block_size))
			threads.append(thread)
	except ftplib.all_errors as e:
		print(e)
		if e.args[0][:3] == '550':
			print(f'[Error]: {remote_file_path} is missing!')
		else:
			print(f'[Error]: Failed to check file size of {remote_file_path}! {e}')
		if fatal: exit(1)
	print(f'[Notice]: Get {remote_file_path} ...')
	if thread_size > 0:
		for i in range(thread_size):
			threads[i].start()
		for i in range(thread_size):
			threads[i].join()
		# Merge part files into one.
		file = open(local_file_path, 'ab')
		for i in range(thread_size):
			part_file_path = f'{local_file_path}.part.{i}'
			file.write(open(part_file_path, 'rb').read())
			os.remove(part_file_path)
	else:
		try:
			# Ensure connection is good.
			ftp = connect()
			ftp.retrbinary(f'RETR {remote_file_path}', open(local_file_path, 'wb').write)
		except ftplib.all_errors as e:
			print('retrbinary ', e)
			if e.args[0][:3] == '550':
				print(f'[Error]: {remote_file_path} does not exist!')
			else:
				print(f'[Error]: Failed to get {remote_file_path}! {e}')
			if fatal: exit(1)

def ftp_get_thread(thread_id, remote_file_path, local_file_path, connect, force, fatal, begin_pos, block_size):
	print(f'==> Thread {thread_id} is downloading {begin_pos}:{begin_pos + block_size} ...')
	ftp = connect()
	ftp.voidcmd('TYPE I')

	local_dir = os.path.dirname(local_file_path)
	part_file = open(f'{local_file_path}.part.{thread_id}', 'wb')

	stream = ftp.transfercmd(f'RETR {remote_file_path}', rest=begin_pos)
	remained_size = block_size
	while True:
		data = stream.recv(remained_size)
		if not data: break
		part_file.write(data)
		remained_size = remained_size - len(data)
		if remained_size == 0: break
	stream.close()
	try:
		ftp.quit()
	except ftplib.all_errors as e:
		#print(f'Failed to quit ftp {thread_id} due to {e}!')
		pass
