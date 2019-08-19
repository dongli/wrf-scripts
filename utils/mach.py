import cli
import os

if not 'WRF_SCRIPTS_QUEUE' in os.environ:
	cli.error('Environment WRF_SCRIPTS_QUEUE should be set by you!')
if not 'WRF_SCRIPTS_NTASKS_PER_NODE' in os.environ:
	cli.error('Environment WRF_SCRIPTS_NTASKS_PER_NODE should be set by you!')
queue = os.environ['WRF_SCRIPTS_QUEUE']
ntasks_per_node = os.environ['WRF_SCRIPTS_NTASKS_PER_NODE']
