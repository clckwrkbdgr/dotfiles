import os, subprocess
import datetime
from collections import namedtuple
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
from clckwrkbdgr import xdg

class Config:
	def __init__(self, taskfile=None, separator=None):
		self.taskfile = Path(taskfile or xdg.save_data_path('taskwarrior')/'tasklist.lst')
		self.separator = separator or ' '

class TaskWarrior:
	Entry = namedtuple('Entry', 'datetime title')

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
	def stop(self):
		with self.config.taskfile.open('a+') as f:
			f.write(datetime.datetime.now().isoformat() + '\n')
		return True
	def get_current_task(self):
		history = iter(self.get_history())
		current = next(history, None)
		for current in history:
			continue
		if current is None:
			return None
		return current.title
	def get_history(self):
		if not self.config.taskfile.exists():
			return
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
				yield self.Entry(
						entry_datetime,
						entry_title,
						)
	def fix_history(self):
		return 0 == subprocess.call([os.environ.get('EDITOR', 'vi'), str(self.config.taskfile)])
