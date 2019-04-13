try:
	import pyslurm
	no_pyslurm = False
except:
	no_pyslurm = True
from job_running import job_running
import cli

def kill_job(job_id):
	if job_running(job_id):
		cli.warning(f'Kill job {job_id}.')
		pyslurm.slurm_kill_job(job_id, 9)
