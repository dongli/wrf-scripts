import subprocess
import re
import os
from time import sleep
import mach
from run import run
from job_running import job_running
from kill_job import kill_job
import cli
import signal
signal.signal(signal.SIGINT, signal.default_int_handler)

def submit_job(cmd, ntasks, config, args, logfile='rsl.out.0000', wait=False):
	if args.ntasks_per_node != None:
		ntasks_per_node = args.ntasks_per_node
	else:
		ntasks_per_node = mach.ntasks_per_node
	if ntasks_per_node != None and ntasks < ntasks_per_node:
		cli.warning(f'Change ntasks_per_node  from {ntasks_per_node} to {ntasks}.')
		ntasks_per_node = ntasks
	if args.slurm:
		f = open('submit.sh', 'w')
		f.write(f'''\
#!/bin/bash
#SBATCH --job-name {config["tag"]}
#SBATCH --comment WRF
#SBATCH --partition {mach.queue}
#SBATCH --time 24:00:00
#SBATCH --ntasks {ntasks}
#SBATCH --ntasks-per-node {ntasks_per_node}
#SBATCH --nodes {int(ntasks / ntasks_per_node)}

mpiexec -np {ntasks} {cmd}
''')
		f.close()
		stdout = run('sbatch < submit.sh', stdout=True)
		match = re.search('Submitted batch job (\w+)', stdout)
		if not match: cli.error(f'Failed to parse job id from {stdout}')
		job_id = match[1]
		cli.notice(f'Job {job_id} submitted running {ntasks} tasks.')
		if wait:
			cli.notice(f'Wait for job {job_id}.')
			try:
				last_line = None
				while job_running(args, job_id):
					sleep(10)
					if not os.path.isfile(logfile): continue
					line = subprocess.run(['tail', '-n', '1', logfile], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
					if last_line != line and line != '':
						last_line = line
						print(f'{cli.cyan("==>")} {last_line if len(last_line) <= 80 else last_line[:80]}')
			except KeyboardInterrupt:
				kill_job(args, job_id)
				exit(1)
		return job_id
	elif args.pbs:
		f = open('submit.sh', 'w')
		f.write(f'''\
#!/bin/bash
#PBS -N {config["tag"]}
#PBS -q {mach.queue}
#PBS -l nodes={int(ntasks / ntasks_per_node)}:ppn={ntasks_per_node}

cd $PBS_O_WORKDIR
mpiexec -np {ntasks} -machinefile $PBS_NODEFILE {cmd}
''')
		f.close()
		stdout = run('qsub < submit.sh', stdout=True)
		match = re.search('(\w+)', stdout)
		if not match: cli.error(f'Failed to parse job id from {stdout}')
		job_id = match[1]
		cli.notice(f'Job {job_id} submitted running {ntasks} tasks.')
		if wait:
			cli.notice(f'Wait for job {job_id}.')
			try:
				last_line = None
				while job_running(args, job_id):
					sleep(10)
					if not os.path.isfile(logfile): continue
					line = subprocess.run(['tail', '-n', '1', logfile], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
					if last_line != line and line != '':
						last_line = line
						print(f'{cli.cyan("==>")} {last_line if len(last_line) <= 80 else last_line[:80]}')
			except KeyboardInterrupt:
				kill_job(args, job_id)
				exit(1)
		return job_id
	else:
		proc = run(f'mpiexec -np {ntasks} {cmd}', bg=True)
		try:
			while proc.poll() == None:
				sleep(10)
				res = subprocess.run(['tail', '-n', '1', logfile], stdout=subprocess.PIPE)
				last_line = res.stdout.decode("utf-8").strip()
				print(f'{cli.cyan("==>")} {last_line if len(last_line) <= 80 else last_line[:80]}')
		except KeyboardInterrupt:
			cli.warning('Ended by user!')
			proc.kill()
			exit(1)
