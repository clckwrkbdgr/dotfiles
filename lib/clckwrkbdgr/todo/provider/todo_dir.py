import clckwrkbdgr.todo
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path

@clckwrkbdgr.todo.task_provider('todo_dir')
def list_todo_directory():
	for entry in clckwrkbdgr.todo.read_config().todo_dir.iterdir():
		if entry == clckwrkbdgr.todo.read_config().inbox_file:
			continue
		yield clckwrkbdgr.todo.Task(entry.name)
