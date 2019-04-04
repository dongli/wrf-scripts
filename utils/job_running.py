import pyslurm
import cli

def job_running(job_id):
	job = pyslurm.job().find_id(job_id)
	if len(job) == 0:
		cli.error(f'Failed to find job {job_id}!')
	elif len(job) > 1:
		cli.error(f'There are more than one job with id {job_id}!')
	job = job[0]
	return job['job_state'] in ('RUNNING', 'PENDING')
