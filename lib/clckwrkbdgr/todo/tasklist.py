import sys, subprocess, platform
import importlib
import logging
logger = logging.getLogger('todo')
from collections import namedtuple
import clckwrkbdgr.todo
import clckwrkbdgr.todo.provider
from clckwrkbdgr import xdg

for entry in clckwrkbdgr.todo.read_config().task_providers: # pragma: no cover -- TODO really shouldn't do this in module's body.
	try:
		importlib.import_module(entry)
	except Exception as e:
		print("Failed to load task provider '{0}': {1}".format(entry, e))

def filter_task_list(original, current):
	""" Checks each line from original list against current.
	Yields pairs (bool, <line>), where bool is True, if line should be kept, and False if line should be removed, and None if it is new line.
	"""
	prev = None
	for line in current:
		if line not in original:
			yield None, line
			prev = line
	for line in original:
		if not line.strip():
			if prev is None:
				logger.debug("Empty line at the beginning, skipping.")
				yield False, line
			elif not prev.strip():
				logger.debug("Consequent empty line, skipping.")
				yield False, line
			else:
				yield True, line
				prev = line
		elif line not in current:
			logger.debug("Task is not present anymore: {0}".format(line))
			yield False, line
		else:
			yield True, line
			prev = line

class TaskList: # pragma: no cover -- TODO depends on global list of task providers, also on FS.
	def __init__(self):
		self._filename = xdg.save_state_path('todo')/'tasklist.lst'
	def sort(self):
		config = clckwrkbdgr.todo.read_config()
		return 0 == subprocess.call(config.editor + [str(self._filename)], shell=(platform.system() == 'Windows'))
	def sync(self):
		logger.debug('Sync...')
		tasks = []
		for provider in clckwrkbdgr.todo.task_provider:
			for task in provider():
				logger.debug('Provider {0}: {1}'.format(provider.__name__ if hasattr(provider, '__name__') else provider, task))
				tasks.append(task.title.encode('utf-8', 'replace'))

		old_lines = []
		if self._filename.exists():
			logger.debug('Reading old lines...')
			old_lines = self._filename.read_bytes().splitlines()
		new_lines = []
		changed = False
		for keep, line in filter_task_list(old_lines, tasks):
			if keep:
				logger.debug('Keeping line: {0}'.format(line))
				new_lines.append(line)
			elif keep is None:
				logger.debug('Adding line: {0}'.format(line))
				new_lines.append(line)
				changed = True
			else: # False
				logger.debug('Removed line: {0}'.format(line))
				changed = True
		if changed:
			logger.debug('Tasklist is changed, rewritting task file...')
			self._filename.write_bytes(b'\n'.join(new_lines).rstrip() + b'\n')
		else:
			logger.debug('Tasklist is NOT changed.')
		logger.debug('Sync done.')
	def list_all(self, with_seps=False):
		if not self._filename.exists():
			return
		for line in self._filename.read_text(errors='replace').splitlines():
			if not with_seps and not line.strip():
				continue
			yield line
