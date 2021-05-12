import sys
import importlib
import clckwrkbdgr.todo
import clckwrkbdgr.todo.provider
from clckwrkbdgr import xdg

for entry in clckwrkbdgr.todo.read_config().task_providers:
	try:
		importlib.import_module(entry)
	except Exception as e:
		print("Failed to load task provider '{0}': {1}".format(entry, e))

class TaskList:
	def __init__(self):
		self._filename = xdg.save_state_path('todo')/'tasklist.lst'
	def sync(self):
		new_lines = []
		for provider in clckwrkbdgr.todo.task_provider:
			for task in provider():
				new_lines.append(task.title)
		self._filename.write_text('\n'.join(new_lines) + '\n')
	def list_all(self):
		if not self._filename.exists():
			return
		for line in self._filename.read_text(errors='replace').splitlines():
			yield line
