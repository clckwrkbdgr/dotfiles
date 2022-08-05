import os
import json
import functools
import importlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
from clckwrkbdgr.collections import AutoRegistry, dotdict
from clckwrkbdgr import xdg
from clckwrkbdgr import utils

class Task:
	def __init__(self, title):
		self.title = title
	def __str__(self):
		return self.title
	def __repr__(self): # pragma: no cover
		return 'Task({0})'.format(repr(self.title))

task_provider = AutoRegistry()

CONFIG_FILE_DESC = """Configuration is stored in $XDG_DATA_HOME/todo/config.json

\b
Fields:
- editor: Command to run editor (list of arguments). Filename will be added to the end of the arg list. Default is [$EDITOR].
- inbox_file: path to INBOX file (may contain tilde and environment variables). Default is "~/.local/share/todo/.INBOX.md"
- prepend_inbox: prepend new items to INBOX file instead of appending it to the end. Default is False (appending to the end).
- todo_dir: entries in this directory will be used for default built-in task provider (clckwrkbdgr.todo.provider.todo_dir).
- task_providers: list of entries; each entry should be either Python module or path to Python file. These files should export functions decorated with @clckwrkbdgr.todo.task_provider(...).
- tasklist: name of fully quialifed Python class; module should be available in sys.path. It will be used instead of default clckwrkbdgr.todo.tasklist.TaskList
"""

@functools.lru_cache()
def read_config(): # pragma: no cover
	config_file = xdg.save_data_path('todo')/'config.json'
	data = {}
	if config_file.exists():
		data = json.loads(config_file.read_text())

	tasklist = None
	tasklist_class_name = data.get('tasklist', None)
	if tasklist_class_name:
		parts = tasklist_class_name.split('.')
		module_names = []
		for part in parts:
			if not module_names:
				module_names.append([part])
			else:
				module_names.append(module_names[-1] + [part])
		tasklist_module = None
		for module_name in reversed(module_names):
			try:
				tasklist_module = importlib.import_module('.'.join(module_name))
				break
			except Exception as e:
				pass
		if tasklist_module:
			module_name = '.'.join(module_name)
			assert tasklist_class_name.startswith(module_name)
			tasklist_class_name = tasklist_class_name[len(module_name)+1:]
			try:
				tasklist = getattr(tasklist_module, tasklist_class_name)
			except Exception as e:
				print("Failed to find custom tasklist class '{0}.{1}': {2}".format(module_name, tasklist_class_name, e))
		else:
			print("Failed to find module for tasklist class '{0}'".format(tasklist_class_name))

	return dotdict(
			inbox_file=Path(os.path.expandvars(data.get('inbox_file', "~/.local/share/todo/.INBOX.md"))).expanduser(),
			prepend_inbox=bool(data.get('prepend_inbox', False)),
			editor=list(data.get('editor', [os.environ.get('EDITOR', 'vim')])),
			todo_dir=Path(os.path.expandvars(data.get('todo_dir', "~/.local/share/todo/"))).expanduser(),
			task_providers=list(data.get('task_providers', [])),
			tasklist=tasklist,
			)
