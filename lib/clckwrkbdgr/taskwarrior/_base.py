import os, subprocess
import datetime
import functools
from collections import namedtuple
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
from clckwrkbdgr import xdg

class Config:
	def __init__(self, taskfile=None, separator=None,
			stop_alias=None, resume_alias=None,
			):
		""" Configuration for task tracker.
		- taskfile: storage file for task history.
		  Default is $XDG_DATA_HOME/taskwarrior/tasklist.lst
		- separator: text separator between date/time field and task title in the task file.
		  Default is space.
		- stop_alias: Task title to put instead of default 'stop' action.
		  By default 'stop' entries will have title=None.
		- resume_alias: Task title to put instead of default 'resume' action.
		  By default 'resume' entries will adopt the title of the last stopped task.
		"""
		self.taskfile = Path(taskfile or xdg.save_data_path('taskwarrior')/'tasklist.lst')
		self.separator = separator or ' '
		self.stop_alias = stop_alias
		self.resume_alias = resume_alias

@functools.total_ordering
class Entry(object):
	def __init__(self, datetime, title, is_resume=False, is_stop=False):
		self.datetime = datetime
		self.title = title
		assert not (is_resume and is_stop)
		self.is_resume = is_resume
		self.is_stop = is_stop
	def __str__(self):
		return '{0} {1}'.format(self.datetime, self.title)
	def __repr__(self):
		args = [repr(self.datetime), repr(self.title)]
		if self.is_resume:
			args.append('is_resume={0}'.format(self.is_resume))
		if self.is_stop:
			args.append('is_stop={0}'.format(self.is_stop))
		return '{0}({1})'.format('Entry', ', '.join(args))
	def __iter__(self):
		return iter((self.datetime, self.title))
	def __lt__(self, other):
		return (self.datetime, self.title) < (other.datetime, other.title)
	def __eq__(self, other):
		return (self.datetime, self.title) == (other.datetime, other.title)
	def __ne__(self, other):
		return (self.datetime, self.title) != (other.datetime, other.title)

class TaskWarrior:
	""" Base interface for Task tracker.
	Current implementation uses plain text file storage.
	"""
	Entry = Entry

	def __init__(self, config=None):
		self.config = config or Config()
	def _append(self, task_datetime, task_title):
		with self.config.taskfile.open('a+') as f:
			line = task_datetime.isoformat() + self.config.separator + str(task_title).replace('\n', ' ') + '\n'
			try:
				f.write(line)
			except UnicodeError: # pragma: no cover
				f.write(line.encode('ascii', 'replace').decode())
	def start(self, task=None, now=None):
		""" Starts new task.
		If task is None, tries to resume previously stopped task. If there were no tasks yet, does nothing and returns False.
		"""
		now = now or datetime.datetime.now()
		if not task:
			task = None
			for current in self.get_history():
				if current.title:
					task = current.title
			if task is None:
				return False
		self._append(now, task)
		return True
	def stop(self, now=None):
		""" Stops current task. """
		now = now or datetime.datetime.now()
		with self.config.taskfile.open('a+') as f:
			f.write(now.isoformat() + '\n')
		return True
	def get_current_task(self):
		""" Returns title of the current task.
		Returns None if there were not tasks or the last entry was 'stop'.
		"""
		current = self.get_current_entry()
		if current is None:
			return None
		return current.title
	def get_current_entry(self):
		""" Returns current task entry or None if there were not tasks yet. """
		history = iter(self.get_history())
		current = next(history, None)
		for current in history:
			continue
		return current
	def filter_history(self,
			start_datetime=None, stop_datetime=None,
			entry_class=None):
		""" Returns filtered task history in form of Entry objects.
		Can filter by:
		- date/time: start_datetime..stop_datetime
		"""
		start_datetime = start_datetime or datetime.datetime.min
		stop_datetime = stop_datetime or datetime.datetime.max
		history = self.get_history(entry_class=entry_class)
		for entry in history:
			if not (start_datetime <= entry.datetime <= stop_datetime):
				continue
			yield entry
	def get_history(self, entry_class=None):
		""" Returns full task history in form of Entry objects. """
		if not self.config.taskfile.exists():
			return
		entry_class = entry_class or self.Entry
		last_started_task_title = '<unknown>'
		with self.config.taskfile.open('r') as f:
			for line in f.readlines():
				if self.config.separator in line:
					entry_datetime, entry_title = line.rstrip('\n').split(self.config.separator, 1)
				elif '\t' in line:
					entry_datetime, entry_title = line.rstrip('\n').split('\t', 1)
				elif ' ' in line:
					entry_datetime, entry_title = line.rstrip('\n').split(' ', 1)
				else:
					entry_datetime, entry_title = line.rstrip('\n'), None
				try:
					entry_datetime = datetime.datetime.strptime(entry_datetime, "%Y-%m-%dT%H:%M:%S.%f")
				except ValueError:
					entry_datetime = datetime.datetime.strptime(entry_datetime, "%Y-%m-%dT%H:%M:%S")

				entry = entry_class(
						entry_datetime,
						entry_title,
						)

				if entry_title is None:
					entry.is_stop = True
				elif self.config.stop_alias and entry_title == self.config.stop_alias:
					entry.title = None
					entry.is_stop = True
				elif self.config.resume_alias and entry_title == self.config.resume_alias:
					entry.title = last_started_task_title
					entry.is_resume = True
				elif entry_title == last_started_task_title:
					entry.is_resume = True

				if not entry_title:
					pass
				elif self.config.resume_alias and entry_title == self.config.resume_alias:
					pass
				elif self.config.stop_alias and entry_title == self.config.stop_alias:
					pass
				else:
					last_started_task_title = entry_title

				yield entry
	def fix_history(self):
		""" Allows to edit task history manually using text editor. """
		return 0 == subprocess.call([os.environ.get('EDITOR', 'vi'), str(self.config.taskfile)])
