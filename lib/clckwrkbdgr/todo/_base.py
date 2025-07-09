import os, sys
import datetime
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

@functools.total_ordering
class Priority(object):
	""" Priority value for ordering tasks within task list.
	Fields in order of value, descending:
	- important: [bool] - crucial task, absolute must; can't live without it.
	- urgent: [bool] - must be done in time manner, cannot be postponed for future.
	- deadline: [date or None] - the closer the date, the more urgent task is; "yesterday" tasks are the most urgent.
	- hard: [bool] - in terms of putting effort; the frog that should be eaten first.
	- order: [int >= 0] - internal sorting order for otherwise similar tasks; the less the value, the more priority it has.
	"""
	def __init__(self, important=False, urgent=False, deadline=None, hard=False, order=float('inf')):
		self._important = bool(important)
		self._urgent = bool(urgent)
		if deadline is not None and not isinstance(deadline, datetime.datetime):
			raise ValueError("Deadline should be either datetime object or None: {0}".format(repr(deadline)))
		self._deadline = deadline
		self._hard = bool(hard)
		if order < 0:
			raise ValueError('Order should be not less than 0: {0}'.format(repr(order)))
		self._order = order
	@property
	def important(self): return self._important
	@property
	def urgent(self): return self._urgent
	@property
	def deadline(self): return self._deadline
	@property
	def hard(self): return self._hard
	@property
	def order(self): return self._order

	def key(self):
		""" Sorting key for priority objects.
		If A.key() > B.key(), A has more priority and should come first.
		"""
		return (
				self._important,
				self._urgent,
				(datetime.datetime.max - self._deadline) if self._deadline else datetime.timedelta(),
				self._hard,
				-self._order,
				)
	def __str__(self):
		return ''.join([
			'!' if self._important else '',
			'U' if self._urgent else '',
			'({0})'.format(self._deadline) if self._deadline else '',
			'*' if self._hard else '',
			':{0}'.format(self._order) if self._order != float('inf') else '',
			])
	def __repr__(self):
		return 'Priority({0})'.format(', '.join(filter(None, [
			'important=True' if self._important else '',
			'urgent=True' if self._urgent else '',
			'deadline={0}'.format(repr(self._deadline)) if self._deadline else '',
			'hard=True' if self._hard else '',
			'order={0}'.format(self._order) if self._order != float('inf') else '',
			])))
	def __hash__(self):
		return hash(self.key())
	def __eq__(self, other):
		return self.key() == other.key()
	def __lt__(self, other):
		return self.key() < other.key()

@functools.total_ordering
class Task(object):
	def __init__(self, title, priority=None, tags=None):
		self.title = title
		self.priority = priority or Priority()
		self.tags = set(map(str, (tags or [])))
	def __str__(self):
		return self.title
	def __repr__(self):
		if self.tags:
			return 'Task({0}, {1}, tags={2})'.format(repr(self.title), repr(self.priority), repr(self.tags))
		return 'Task({0}, {1})'.format(repr(self.title), repr(self.priority))
	def __hash__(self):
		return hash((self.title, self.priority, tuple(sorted(self.tags))))
	def __eq__(self, other):
		return (self.title, self.priority, self.tags) == (other.title, other.priority, self.tags)
	def __lt__(self, other):
		return (self.priority, self.title) < (other.priority, other.title)

task_provider = AutoRegistry()

CONFIG_FILE_DESC = """Configuration is stored in $XDG_CONFIG_HOME/local/todo/config.json
Optional configuration file is keeped for backward compatibility at $XDG_DATA_HOME/todo/config.json

\b
Fields:
- editor: Command to run editor (list of arguments). Filename will be added to the end of the arg list. Default is [$EDITOR].
- inbox_file: path to INBOX file (may contain tilde and environment variables). Default is "~/.local/share/todo/.INBOX.md"
- prepend_inbox: prepend new items to INBOX file instead of appending it to the end. Default is False (appending to the end).
- todo_dir: entries in this directory will be used for default built-in task provider (clckwrkbdgr.todo.provider.todo_dir).
- task_providers: list of entries; each entry should be either Python module or path to Python file. These files should export functions decorated with @clckwrkbdgr.todo.task_provider(...).
- tasklist: name of fully quialifed Python class; module should be available in sys.path. It will be used instead of default clckwrkbdgr.todo.tasklist.TaskList
- pager: use pager to display todo list. Either pager, command or bool (in case of True will try to autodetect available pager).
- todo_separator_color: termcolor-recognizable color name to use for underlines between groups in todo list. Default is autocolor (usually white).
"""

@functools.lru_cache()
def read_config(config_file=None):
	if config_file: # pragma: no cover -- TODO
		config_file = Path(config_file)
	else: # pragma: no cover -- TODO
		config_file = xdg.save_data_path('todo')/'config.json'
		if not config_file.exists():
			config_file = xdg.save_config_path('local/todo')/'config.json'
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
			except Exception as e: # pragma: no cover
				print("Failed to find custom tasklist class '{0}.{1}': {2}".format(module_name, tasklist_class_name, e))
		else: # pragma: no cover
			print("Failed to find module for tasklist class '{0}'".format(tasklist_class_name))

	return dotdict(
			inbox_file=Path(os.path.expandvars(data.get('inbox_file', "~/.local/share/todo/.INBOX.md"))).expanduser(),
			prepend_inbox=bool(data.get('prepend_inbox', False)),
			pager=data.get('pager', False),
			editor=list(data.get('editor', [os.environ.get('EDITOR', 'vim')])),
			todo_dir=Path(os.path.expandvars(data.get('todo_dir', "~/.local/share/todo/"))).expanduser(),
			task_providers=list(data.get('task_providers', [])),
			todo_separator_color=data.get('todo_separator_color', None),
			tasklist=tasklist,
			)
