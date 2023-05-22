import os, subprocess
import datetime
import json
import functools, itertools
import tempfile, shutil
from collections import namedtuple
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
import six
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
	@classmethod
	@functools.lru_cache()
	def read_config(cls, filename=None): # pragma: no cover -- TODO
		""" Reads configuration from JSON file.
		Default location is XDG_DATA_PATH/taskwarrior/config.json
		If file does not exist, returns default configuration values.
		For possible configuration fields see documentation of Config class.
		"""
		filename = Path(filename or xdg.save_data_path('taskwarrior')/'config.json')
		data = {}
		if filename.exists():
			data = json.loads(filename.read_text())
		taskfile = data.get('taskfile')
		if taskfile:
			taskfile = os.path.expanduser(taskfile)
		return cls(
				taskfile=taskfile,
				separator=data.get('separator'),
				stop_alias=data.get('stop_alias'),
				resume_alias=data.get('resume_alias'),
				)

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

class Stat(object):
	def __init__(self, start, stop, title):
		assert start < stop, "{0}..{1} {2}".format(start, stop, title)
		self.start = start
		self.stop = stop
		assert title, "{0}..{1} {2}".format(start, stop, title)
		self.title = title
	def __str__(self):
		return '{0} {1}'.format(self.passed, self.title)
	def __repr__(self):
		args = [repr(self.start), repr(self.stop), repr(self.title)]
		return '{0}({1})'.format('Stat', ', '.join(args))
	@property
	def passed(self):
		return self.stop - self.start
	def __eq__(self, other):
		return (self.passed, self.title) == (other.passed, other.title)
	def __ne__(self, other):
		return (self.passed, self.title) != (other.passed, other.title)

class TaskWarrior:
	""" Base interface for Task tracker.
	Current implementation uses plain text file storage.
	"""
	Entry = Entry
	Stat = Stat

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
		if self.config.taskfile.exists():
			total_history = list(self._parse_history(self.config.taskfile, self.config.separator))
			if total_history and total_history[-1][0] == now:
				if total_history[-1][1] == task:
					return True # Already have the same task with the same time added.
				now += datetime.timedelta(seconds=1) # Otherwise it is a new task, but it should have slightly different start time.
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
	def get_stats(self, start_datetime=None, stop_datetime=None,
			squeeze=False,
			stat_class=None):
		""" Yields tracked Stat objects for each task in history.
		If start_datetime and/or stop_datetime are specified,
		stats are bound to given time frame.
		Resulting passed time for tasks that are on bounds (if any)
		is limited to the time that fit into given time frame.
		If squeeze is True, joins all consequent stats for the same task.
		"""
		start_datetime = start_datetime or datetime.datetime.min
		stop_datetime = stop_datetime or datetime.datetime.now()
		yield_queue = []
		for stat in self._iter_raw_stats(now=stop_datetime, stat_class=stat_class):
			if stat.start < start_datetime and stat.stop < start_datetime:
				continue
			if stop_datetime < stat.start and stop_datetime < stat.stop:
				continue
			if stat.start <= start_datetime <= stat.stop:
				stat.start = start_datetime
			if stat.start <= stop_datetime <= stat.stop:
				stat.stop = stop_datetime
			if stat.start == stat.stop:
				continue
			if squeeze:
				if yield_queue and yield_queue[-1].title == stat.title and yield_queue[-1].stop == stat.start:
					yield_queue[-1].stop = stat.stop
				else:
					for _ in yield_queue:
						yield _
					yield_queue = [stat]
			else:
				yield stat
		for stat in yield_queue:
			yield stat
	def accumulate_stats(self, start_datetime=None, stop_datetime=None,
			stat_class=None):
		""" Yields accumulated Stat values for each unique task in history (or given timeframe) ordered by title.
		Start and stop times of generated Stat object may become meaningless. Only .passed will be valid.
		"""
		stats = list(self.get_stats(
			start_datetime=start_datetime,
			stop_datetime=stop_datetime,
			squeeze=True,
			stat_class=stat_class,
			))
		current = None
		for stat in sorted(stats, key=lambda _: _.title):
			if not current:
				current = stat
				continue
			if stat.title == current.title:
				current.stop += (stat.stop - stat.start)
			else:
				yield current
				current = stat
		if current:
			yield current
	def _iter_raw_stats(self, now=None, stat_class=None):
		now=now or datetime.datetime.now()
		stat_class = stat_class or self.Stat
		def pairwise(seq):
			first, second = itertools.tee(seq)
			next(second, None)
			return six.moves.zip(first, second)
		entry = None
		for prev, entry in pairwise(self.get_history()):
			if not prev.title:
				continue
			yield stat_class(prev.datetime, entry.datetime, prev.title)
		if entry and entry.title and entry.datetime < now:
			yield stat_class(entry.datetime, now, entry.title)
	def filter_history(self,
			start_datetime=None, stop_datetime=None,
			only_breaks=False,
			squeeze_breaks=False,
			entry_class=None):
		""" Returns filtered task history in form of Entry objects.
		Can filter by:
		- date/time: start_datetime..stop_datetime
		- only_breaks: return only stop/resume events and only in pairs,
		  e.g. stop with consequent start of new task is not considered a break.
		- squeeze_breaks: compact consequent pairs of break events into a single break.
		"""
		start_datetime = start_datetime or datetime.datetime.min
		stop_datetime = stop_datetime or datetime.datetime.max
		def with_prev(it):
			prev = None
			for _ in it:
				yield _, prev
				prev = _
		history = with_prev(self.get_history(entry_class=entry_class))
		QUEUE_SIZE = 3
		yield_queue = []
		for entry, prev in history:
			if entry.is_stop and prev and prev.is_stop:
				continue
			if entry.is_resume and prev and prev.is_resume: # pragma: no cover -- should not ever happen, but still as a precaution.
				continue
			if not (start_datetime <= entry.datetime <= stop_datetime):
				continue
			if squeeze_breaks:
				if entry.is_resume and len(yield_queue) >= 3 and yield_queue[-1].is_stop and yield_queue[-2].is_resume and yield_queue[-2].title == entry.title and yield_queue[-3].is_stop:
					yield_queue.pop(-1)
					yield_queue.pop(-1)
			if only_breaks:
				if not entry.is_resume and yield_queue and yield_queue[-1].is_stop:
					yield_queue.pop(-1)
				if not (entry.is_resume or entry.is_stop):
					continue
			yield_queue.append(entry)
			while len(yield_queue) > QUEUE_SIZE:
				yield yield_queue.pop(0)
		if only_breaks and yield_queue and yield_queue[-1].is_stop:
			yield_queue.pop(-1)
		while yield_queue:
			yield yield_queue.pop(0)
	@staticmethod
	def _parse_history(filename, separator):
		""" Yields raw pairs (datetime, title). """
		with filename.open('r') as f:
			for line in f.readlines():
				if separator in line:
					entry_datetime, entry_title = line.rstrip('\n').split(separator, 1)
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
				yield entry_datetime, entry_title
	def get_history(self, entry_class=None):
		""" Returns full task history in form of Entry objects. """
		if not self.config.taskfile.exists():
			return
		entry_class = entry_class or self.Entry
		last_started_task_title = '<unknown>'
		prev = None
		for entry_datetime, entry_title in self._parse_history(self.config.taskfile, self.config.separator):
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
			elif entry_title == last_started_task_title and prev and prev.is_stop:
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
			prev = entry
	def rewrite_history(self, start_datetime, stop_datetime, new_titles, fill_value=None):
		""" Rewrites part of task history in given time frame (including boundaries).
		Replaces all tasks within time frame with corresponding title from given list.
		If title is None, a stop is created instead.
		Number of titles should match number of actual tasks in the time frame, otherwise RuntimeError is raised.
		Unless fill_value is specified, which is used in case when there were not enough titles to cover the time frame.
		Creates backup version in XDG_STATE_HOME/taskwarrior/taskfile.bak
		"""
		new_taskfile = tempfile.NamedTemporaryFile(mode='w', delete=False)
		new_titles_count = 0
		try:
			with new_taskfile as fobj:
				for entry_datetime, entry_title in self._parse_history(self.config.taskfile, self.config.separator):
					if start_datetime <= entry_datetime <= stop_datetime:
						if not new_titles:
							if fill_value:
								entry_title = fill_value
							else:
								raise RuntimeError('Not enough titles specified for the time frame {0}..{1}: got only {2}'.format(
									start_datetime, stop_datetime,
									new_titles_count,
									))
						else:
							entry_title = new_titles.pop(0)
						new_titles_count += 1
					if entry_title:
						line = '{0}{2}{1}\n'.format(entry_datetime.isoformat(), entry_title, self.config.separator)
					else:
						line = '{0}\n'.format(entry_datetime.isoformat())
					try:
						fobj.write(line)
					except UnicodeError: # pragma: no cover
						fobj.write(line.encode('ascii', 'replace').decode())
			if new_titles:
				raise RuntimeError('{0} unused titles left after replacing entries in the time frame {1}..{2}'.format(len(new_titles),
					start_datetime, stop_datetime))
			shutil.copy(str(self.config.taskfile), str(xdg.save_state_path('taskwarrior')/'taskfile.bak'))
			shutil.move(str(new_taskfile.name), str(self.config.taskfile))
		finally:
			if os.path.exists(str(new_taskfile.name)):
				os.unlink(str(new_taskfile.name))
	def fix_history(self):
		""" Allows to edit task history manually using text editor. """
		return 0 == subprocess.call([os.environ.get('EDITOR', 'vi'), str(self.config.taskfile)])
