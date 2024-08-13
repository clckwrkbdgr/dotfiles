import os
from ..messages import Log

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
	def load(self, loader):
		if not self.exists():
			return None
		Log.debug('Loading savefile: {0}...'.format(self.FILENAME))
		with open(self.FILENAME, 'r') as f:
			data = f.read().split('\0')
		data = iter(data)
		return loader(data)
	def save(self, saver):
		with open(self.FILENAME, 'w') as f:
			first = True
			for item in saver():
				if not first:
					f.write('\0')
				f.write(str(item))
				first = False
	def unlink(self):
		if not self.exists():
			return
		os.unlink(self.FILENAME)
