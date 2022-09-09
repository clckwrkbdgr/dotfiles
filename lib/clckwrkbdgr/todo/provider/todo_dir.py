from .. import _base as todo
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
from ... import xdg

@todo.task_provider('todo_dir')
def list_todo_directory():
	for entry in todo.read_config().todo_dir.iterdir():
		if entry == todo.read_config().inbox_file:
			continue
		if entry == xdg.save_data_path('todo')/'config.json':
			continue
		yield todo.Task(entry.name, tags=[entry.stem.split('.')[-1]])
