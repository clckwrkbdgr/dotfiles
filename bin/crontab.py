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
from clckwrkbdgr.commands import run_command_and_collect_output

DATABASE_FILE = Path(os.environ['USERPROFILE'])/'crontab.db'

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
def command_daemon(): # pragma: no cover -- TODO use crontab.run_scheduler()
	""" Not actually a daemon per se, not even nearly.
	Just loads schedules and checks them against timestamp file.
	Then runs jobs that are qualified via function job_filter(commandline)
	and are to be triggered between last run and current date
	Updates timestamp file.
	"""
	last_run = datetime.datetime.now()
	last_run = last_run.replace(second=0)
	logging.debug("Starting: {0}".format(last_run))
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
			os.environ[k] = v

		logging.debug("Last run: {0}".format(last_run))
		logging.debug("Now: {0}".format(now))
		commands_to_run = []
		for job in jobs:
			logging.debug(job)
			schedule = job.schedule(last_run)
			next_time = schedule.get_next()
			logging.debug("    Next time: {0}".format(next_time))
			if last_run < next_time < now:
				logging.debug("    Should fire.")
				command = shlex.split(job.command)
				logging.debug('    ' + str(command))
				command = list(map(os.path.expanduser, map(str, command)))
				commands_to_run.append(command)

		last_run = now
		for command in commands_to_run:
			logging.debug("Running threaded command: {0}".format(command))
			thread = threading.Thread(target=run_command_and_collect_output, args=(command, Path.home()))
			thread.start()

if __name__ == '__main__':
	cli()
