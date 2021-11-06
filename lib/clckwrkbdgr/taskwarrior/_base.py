import os, subprocess
import datetime
from collections import namedtuple
from clckwrkbdgr import xdg

class TaskWarrior:
	Entry = namedtuple('Entry', 'datetime title')

	def __init__(self):
		self._taskfile = xdg.save_data_path('taskwarrior')/'tasklist.lst'
	def start(self, task=None):
		if not task:
			task = None
			for current in self.get_history():
				if current.title:
					task = current.title
			if task is None:
				return False
		with self._taskfile.open('a+') as f:
			f.write(datetime.datetime.now().isoformat() + ' ' + str(task).replace('\n', ' ') + '\n')
		return True
	def stop(self):
		with self._taskfile.open('a+') as f:
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
		if not self._taskfile.exists():
			return
		with self._taskfile.open('r') as f:
			for line in f.readlines():
				if ' ' in line:
					entry_datetime, entry_title = line.rstrip('\n').split(' ', 1)
				else:
					entry_datetime, entry_title = line.rstrip('\n'), None
				yield self.Entry(
						datetime.datetime.strptime(entry_datetime, "%Y-%m-%dT%H:%M:%S.%f"),
						entry_title,
						)
	def fix_history(self):
		return 0 == subprocess.call([os.environ.get('EDITOR', 'vi'), str(self._taskfile)])
