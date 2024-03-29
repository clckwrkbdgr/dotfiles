#!/usr/bin/env python
""" Crontab-like service for Windows.
Requires `crontab` module:

	pip install python-crontab

"""
import os, sys, subprocess
import shlex
import time, datetime
import pickle
import logging
Log = logging.getLogger('crontab')
import threading
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
import click, click_default_group
try:
	sys.path.remove(os.path.abspath(os.path.dirname(__file__))) # Absolute import should not import THIS crontab.py but the one from the dist.
except:
	pass
import crontab
from clckwrkbdgr.winnt.schtasks import run_immediately
import clckwrkbdgr.logging

DATABASE_FILE = Path(os.environ['LOCALAPPDATA'])/'crontab.db' # FIXME Use XDG_STATE_HOME for Windows.

@click.group(cls=click_default_group.DefaultGroup, default='auto', default_if_no_args=True)
def cli(**extra):
	pass

@cli.command()
@click.option('-l', '--list', 'list_jobs', is_flag=True, default=False, help="Lists currently scheduled jobs.")
@click.argument('crontab_file', required=False, default=None)
def auto(crontab_file=None, list_jobs=False): # pragma: no cover
	""" Performs traditional Unix crontab actions (see --help). """
	if list_jobs:
		if not DATABASE_FILE.is_file():
			return
		for job in pickle.loads(DATABASE_FILE.read_bytes()):
			print(job)
		return True
	if crontab_file:
		content = Path(crontab_file).read_text()
	else:
		content = sys.stdin.read()
	jobs = crontab.CronTab(tab=content)
	DATABASE_FILE.write_bytes(pickle.dumps(jobs))

@cli.command('open')
def command_open(): # pragma: no cover
	""" Opens Windows Scheduler. """
	subprocess.Popen("Taskschd.msc", shell=True)
	return True

@cli.command('daemon')
@click.option('--debug', is_flag=True, help="Show debug traces.")
@click.option('-L', '--logdir', default=Path.home(), type=Path, help="Directory to store report logs for executed jobs.")
def command_daemon(logdir, debug=False): # pragma: no cover -- TODO use crontab.run_scheduler()
	""" Not actually a daemon per se, not even nearly.
	Just loads schedules and checks them against timestamp file.
	Then runs jobs that are qualified via function job_filter(commandline)
	and are to be triggered between last run and current date
	Updates timestamp file.

	All environment variables defined in crontab file will be loaded in global environment and passed to every executed job.
	The only exception is PRIORITY which works only for the job it is defined before. It is a priority of Windows Task Scheduler task and value should be integer within range [4;7].
	See <https://docs.microsoft.com/en-us/windows/win32/taskschd/tasksettings-priority> for details.
	"""
	clckwrkbdgr.logging.init(Log, debug=debug)
	last_run = datetime.datetime.now()
	last_run = last_run.replace(second=0)
	Log.debug("Starting: {0}".format(last_run))
	while True:
		now = datetime.datetime.now()
		minute_is_up = now.second == 0 and now - last_run > datetime.timedelta(seconds=50)
		if not minute_is_up:
			time.sleep(0.5)
			continue

		jobs = pickle.loads(DATABASE_FILE.read_bytes())
		# Hack to retrieve crontab environment.
		# Python-crontab appends env vars to the random jobs for some reason.
		env = {}
		for job in jobs:
			env.update(job.env)
		for k, v in env.items():
			if k == 'PRIORITY': # Job-specific variable
				continue
			os.environ[k] = v

		Log.debug("Last run: {0}".format(last_run))
		Log.debug("Now: {0}".format(now))
		commands_to_run = []
		for job in jobs:
			Log.debug(job)
			schedule = job.schedule(last_run)
			next_time = schedule.get_next()
			Log.debug("    Next time: {0}".format(next_time))
			if last_run < next_time < now:
				Log.debug("    Should fire.")
				command = shlex.split(job.command)
				Log.debug('    ' + str(command))
				command = list(map(os.path.expanduser, map(str, command)))
				commands_to_run.append( (command, job.env) )

		last_run = now
		for command, command_env in commands_to_run:
			try:
				command = subprocess.list2cmdline(command)
				Log.debug("Running: {0}".format(repr(command)))
				priority = command_env.get('PRIORITY')
				if priority:
					Log.debug("With priority: {0}".format(repr(priority)))
					run_immediately(command, 'crontab', logdir, priority=int(priority))
				else:
					run_immediately(command, 'crontab', logdir)
			except:
				import traceback
				try:
					traceback.print_exc()
				except:
					pass

if __name__ == '__main__':
	cli()
