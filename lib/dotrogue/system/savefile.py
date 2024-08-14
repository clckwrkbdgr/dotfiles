import os
import contextlib
from ..messages import Log

class Reader:
	def __init__(self, stream):
		self.stream = stream
		self.version = int(self.read())
	def read(self):
		return next(self.stream)

class Writer:
	def __init__(self, f, version):
		self.version = version
		self.f = f
		self.f.write(str(version))
	def write(self, item):
		self.f.write('\0')
		self.f.write(str(item))

class Savefile:
	FILENAME = os.path.expanduser('~/.rogue.sav')
	@classmethod
	def exists(cls):
		return os.path.exists(cls.FILENAME)
	@classmethod
	def last_save_time(cls):
		if not cls.exists():
			return 0
		return os.stat(cls.FILENAME).st_mtime
	def load(self):
		if not self.exists():
			return None
		Log.debug('Loading savefile: {0}...'.format(self.FILENAME))
		with open(self.FILENAME, 'r') as f:
			data = f.read().split('\0')
		data = iter(data)
		return Reader(data)
	@contextlib.contextmanager
	def save(self, version):
		try:
			with open(self.FILENAME, 'w') as f:
				yield Writer(f, version)
		except:
			self.unlink()
			raise
	def unlink(self):
		if not self.exists():
			return
		os.unlink(self.FILENAME)
