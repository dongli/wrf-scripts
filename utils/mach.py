import cli
import os

queue = None
ntasks_per_node = None
if not 'WRF_SCRIPTS_QUEUE' in os.environ:
	cli.warning('Environment WRF_SCRIPTS_QUEUE is not set. Will run executable in current node!')
elif not 'WRF_SCRIPTS_NTASKS_PER_NODE' in os.environ:
	cli.error('Environment WRF_SCRIPTS_NTASKS_PER_NODE should be set by you!')
else:
	queue = os.environ['WRF_SCRIPTS_QUEUE']
	ntasks_per_node = os.environ['WRF_SCRIPTS_NTASKS_PER_NODE']

if queue != None:
	# Allow user to set multiple queues with descending priority.
	queue = queue.split(',')
	ntasks_per_node = [int(x) for x in ntasks_per_node.split(',')]
