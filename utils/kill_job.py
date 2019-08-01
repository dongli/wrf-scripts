from job_running import job_running
import cli
from run import run

def kill_job(args, job_id):
	if job_running(args, job_id):
		cli.warning(f'Kill job {job_id}.')
		if args.slurm:
			run(f'scancel {job_id}')
		elif args.pbs:
			run(f'qdel {job_id}')
