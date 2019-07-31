from job_running import job_running
import cli
from run import run

def kill_job(args, job_id):
	if job_running(job_id):
		cli.warning(f'Kill job {job_id}.')
		if args.slurm:
			run(f'scancel {job_id}')
		elif args.pbs:
			cli.error('Underconstruction!')
