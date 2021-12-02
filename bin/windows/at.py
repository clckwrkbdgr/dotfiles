import sys, subprocess
import datetime, time
import clckwrkbdgr.winnt.schtasks
import click

@click.command()
@click.option('-l', 'list_jobs', is_flag=True, help='List scheduled jobs')
@click.option('-r', 'remove_job', type=int, help='Remove specified job.')
@click.argument('scheduled_time', required=False)
def cli(scheduled_time=None, list_jobs=False, remove_job=None):
	""" Wrapper for Windows `schtasks` to provide interface similar to Unix `at`.

	Jobs are added as usual like with `at`:

		echo "command ..." | at HH:MM

	Currently only CMD interpreter is supported (with all its drawbacks) and only HH:MM for time format.

	Additionally can list (`at -l`, like `atq`) and remove (`at -r`, like `atrm`) jobs.
	"""
	if list_jobs:
		now = datetime.datetime.now()
		for job in clckwrkbdgr.winnt.schtasks.TaskScheduler().iter_all():
			if not job.registration_info.uri.startswith('\\At\\'):
				continue
			time_trigger = next(trigger for trigger in job.triggers if isinstance(trigger, clckwrkbdgr.winnt.schtasks.TaskScheduler.Trigger.TimeTrigger))
			trigger_time = datetime.datetime.strptime(time_trigger.start_boundary, '%Y-%m-%dT%H:%M:%S')
			if trigger_time < now:
				continue
			action_exec = next(action for action in job.actions if isinstance(action, clckwrkbdgr.winnt.schtasks.TaskScheduler.Action.Exec))
			print('\t'.join([
				job.registration_info.uri.split('\\')[2],
				str(trigger_time),
				job.registration_info.author,
				action_exec.command,
				action_exec.arguments,
				]))
		return
	if remove_job:
		rc = subprocess.call(['schtasks', '/delete', '/f', '/tn', 'At\\{0}'.format(remove_job)])
		sys.exit(rc)
	if not scheduled_time:
		print('Time is not specified', file=sys.stderr)
		return
	job_id = str(int(time.time()))
	command = sys.stdin.read().strip()
	if command.startswith('"') and command.endswith('"'):
		command = command[1:-1]
	if '\n' in command:
		raise RuntimeError("Windows scheduled CMD jobs do not support multi-line shell commands yet.")
	command = "pythonw -m clckwrkbdgr.commands {0}".format(subprocess.list2cmdline(['cmd', '/c', command]))
	rc = subprocess.call(['schtasks', '/create', '/tn', 'At\\{0}'.format(job_id), '/sc', 'once', '/tr', command, '/st', scheduled_time])
	sys.exit(rc)

if __name__ == '__main__':
	cli()
