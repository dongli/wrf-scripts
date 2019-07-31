import re
import cli
from run import run

def job_running(args, job_id):
	if args.slurm:
		stdout = run(f'scontrol show jobid -dd {job_id} | grep JobState', stdout=True, echo=False)
		return re.search('JobState=RUNNING', stdout) != None or re.search('JobState=PENDING', stdout) != None
	elif args.pbs:
		cli.error('Underconstruction!')
