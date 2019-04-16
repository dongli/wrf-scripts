try:
	import pyslurm
	no_pyslurm = False
except:
	no_pyslurm = True
import subprocess
import re
from time import sleep
import mach
from run import run
from job_running import job_running
from kill_job import kill_job
import cli
import signal
signal.signal(signal.SIGINT, signal.default_int_handler)

def submit_job(cmd, ntasks, config, args, logfile='rsl.out.0000', wait=False):
	if args.slurm and not no_pyslurm:
		job_opts = {
			'job_name': config['tag'],
			'comment': 'WRF',
			'partition': mach.queue,
			'time': '24:00:00',
			'ntasks': ntasks,
			'ntasks_per_node': mach.ntasks_per_node,
			'nodes': int(ntasks / mach.ntasks_per_node),
			'exclusive': True,
			'wrap': f'mpiexec -np {ntasks} {cmd}'
		}
		job_id = pyslurm.job().submit_batch_job(job_opts)
		cli.notice(f'Job {job_id} submitted running {ntasks} tasks.')
		if wait:
			cli.notice(f'Wait for job {job_id}.')
			try:
				last_line = None
				while job_running(job_id):
					sleep(10)
					line = subprocess.run(['tail', '-n', '1', logfile], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
					if last_line != line and line != '':
						last_line = line
						print(f'{cli.cyan("==>")} {last_line}')
			except KeyboardInterrupt:
				kill_job(job_id)
				exit(1)
		return job_id
	else:
		proc = run(f'mpiexec -np {args.np} {cmd}', bg=True)
		try:
			while proc.poll() == None:
				sleep(10)
				res = subprocess.run(['tail', '-n', '1', logfile], stdout=subprocess.PIPE)
				print(f'{cli.cyan("==>")} {res.stdout.decode("utf-8").strip()}')
		except KeyboardInterrupt:
			cli.warning('Ended by user!')
			proc.kill()
			exit(1)
