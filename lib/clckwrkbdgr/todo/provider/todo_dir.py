import clckwrkbdgr.todo
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

@clckwrkbdgr.todo.task_provider('todo_dir')
def list_todo_directory(): # pragma: no cover -- TODO accesses FS and config directly.
	for entry in clckwrkbdgr.todo.read_config().todo_dir.iterdir():
		if entry == clckwrkbdgr.todo.read_config().inbox_file:
			continue
		yield clckwrkbdgr.todo.Task(entry.name)
