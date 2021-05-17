import sys, subprocess, platform
import importlib
import logging
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
				logging.debug("Empty line at the beginning, skipping.")
				yield False, line
			elif not prev.strip():
				logging.debug("Consequent empty line, skipping.")
				yield False, line
			else:
				yield True, line
				prev = line
		elif line not in current:
			logging.debug("Task is not present anymore: {0}".format(line))
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
		tasks = []
		for provider in clckwrkbdgr.todo.task_provider:
			for task in provider():
				tasks.append(task.title.encode('utf-8', 'replace'))

		old_lines = []
		if self._filename.exists():
			old_lines = self._filename.read_bytes().splitlines()
		new_lines = []
		changed = False
		for keep, line in filter_task_list(old_lines, tasks):
			if keep or keep is None:
				new_lines.append(line)
			if not keep:
				changed = True
		if changed:
			self._filename.write_bytes(b'\n'.join(new_lines).rstrip() + b'\n')
	def list_all(self, with_seps=False):
		if not self._filename.exists():
			return
		for line in self._filename.read_text(errors='replace').splitlines():
			if not with_seps and not line.strip():
				continue
			yield line
