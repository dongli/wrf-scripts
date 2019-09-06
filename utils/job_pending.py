import re
import cli
from run import run

def job_pending(args, job_id):
	if args.slurm:
		stdout = run(f'scontrol show jobid -dd {job_id} | grep JobState', stdout=True, echo=False)
		return re.search('JobState=PENDING', stdout) != None
	elif args.pbs:
		stdout = run(f'qstat -f {job_id}', stdout=True, echo=False)
		return re.search('job_state = Q', stdout) != None
