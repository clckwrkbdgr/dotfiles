import sys, subprocess, platform
import importlib
import itertools
import logging
logger = logging.getLogger('todo')
from collections import namedtuple
import vintage
from . import _base as todo
from . import provider as default_provider_module
from clckwrkbdgr import xdg

def force_load_task_providers(providers=None): # pragma: no cover -- TODO really shouldn't do this in module's body.
	""" Loads all known task providers (registered via @task_provider).
	If providers are given (list of module names), they are loaded instead.
	"""
	for entry in (providers or todo.read_config().task_providers):
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

class TaskList:
	def __init__(self, _providers=None):
		force_load_task_providers(providers=_providers)
		self._filename = xdg.save_state_path('todo')/'tasklist.lst'
	def sort(self):
		config = todo.read_config()
		return 0 == subprocess.call(config.editor + [str(self._filename)], shell=(platform.system() == 'Windows'))
	def sync(self):
		logger.debug('Sync...')
		tasks = []
		for provider in todo.task_provider:
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
	def list_all(self, with_seps=False, with_groups=False):
		if with_seps: # pragma: no cover -- deprecated
			vintage.warn_deprecation('Argument with_seps is deprecated, use with_groups instead.', frame_correction=1)
			with_groups = True
		if not self._filename.exists():
			return

		grouped_tasks = [[]]
		for line in self._filename.read_text(errors='replace').splitlines():
			if not line.strip():
				grouped_tasks.append([])
			else:
				grouped_tasks[-1].append(todo.Task(line))

		if not with_groups or len(grouped_tasks) == 1:
			grouped_tasks = list(itertools.chain.from_iterable(grouped_tasks))
		grouped_tasks = [item[0] if isinstance(item, list) and len(item) == 1 else item for item in grouped_tasks]

		for item in grouped_tasks:
			yield item
