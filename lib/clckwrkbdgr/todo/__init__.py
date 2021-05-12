import os
import json
import functools
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr.collections import AutoRegistry, dotdict
from clckwrkbdgr import xdg

class Task:
	def __init__(self, title):
		self.title = title
	def __str__(self):
		return self.title
	def __rerp__(self):
		return 'Task({0})'.format(repr(self.title))

task_provider = AutoRegistry()

CONFIG_FILE_DESC = """Configuration is stored in $XDG_DATA_HOME/todo/config.json

\b
Fields:
- editor: Command to run editor (list of arguments). Filename will be added to the end of the arg list. Default is [$EDITOR].
- inbox_file: path to INBOX file (may contain tilde and environment variables). Default is "~/.local/share/todo/.INBOX.md"
- todo_dir: entries in this directory will be used for default built-in task provider (clckwrkbdgr.todo.provider.todo_dir).
- task_providers: list of entries; each entry should be either Python module or path to Python file. These files should export functions decorated with @clckwrkbdgr.todo.task_provider(...).
"""

@functools.lru_cache()
def read_config():
	config_file = xdg.save_data_path('todo')/'config.json'
	data = {}
	if config_file.exists():
		data = json.loads(config_file.read_text())
	return dotdict(
			inbox_file=Path(os.path.expandvars(data.get('inbox_file', "~/.local/share/todo/.INBOX.md"))).expanduser(),
			editor=list(data.get('editor', [os.environ.get('EDITOR', 'vim')])),
			todo_dir=Path(os.path.expandvars(data.get('todo_dir', "~/.local/share/todo/"))).expanduser(),
			task_providers=list(data.get('task_providers', [])),
			)
