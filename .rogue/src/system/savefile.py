import os
import contextlib
from .logging import Log

class AutoSavefile:
	""" Context manager to automatically load/save object from savefile.

	Usage:

	>>> with AutoSavefile() as savefile:
	>>> 	<load obj from savefile.reader>
	>>> 	<main actions>
	>>> 	savefile.save(<obj>, <version>)
	"""
	def __init__(self, savefile=None):
		""" Creates new savefile or uses given one. """
		self.savefile = savefile or Savefile()
		self.obj = None
	def __enter__(self):
		""" Opens reader and sets field .reader """
		self.reader = self.savefile.load()
		return self
	def save(self, obj, version):
		""" Call it to finalize saving process. """
		self.obj = obj
		self.version = version
	def __exit__(self, *_t):
		""" Saves object that was passed to save() or unlinks file otherwise. """
		if self.obj:
			with self.savefile.save(self.version) as writer:
				self.obj.save(writer)
		else:
			self.savefile.unlink()

class Reader:
	""" Provides read access to savefile.
	Savefile version is available as field .version
	"""
	def __init__(self, stream):
		""" Initializes reader over stream and reads version.
		"""
		self.stream = stream
		self.version = int(self.read())
	def read(self):
		""" Reads current value from stream (RAW). """
		return next(self.stream)

class Writer:
	""" Provides read access to savefile.
	Savefile version is available as field .version
	"""
	def __init__(self, f, version):
		""" Initializes writer over stream and writes version.
		"""
		self.version = version
		self.f = f
		self.f.write(str(version))
	def write(self, item):
		""" Writes string representation of item to the file. """
		self.f.write('\0')
		self.f.write(str(item))

class Savefile:
	""" Versioned save file to serialize/deserialize objects.
	Provides wrapper interface for Reader/Writer objects.

	Default implementation is a text file: set of string values separated by NULL character.

	See load()/save()
	"""
	FILENAME = os.path.expanduser('~/.rogue.sav')
	@classmethod
	def exists(cls):
		""" Should return True if file exists. """
		return os.path.exists(cls.FILENAME)
	@classmethod
	def last_save_time(cls):
		""" Should return mtime of the existing file, or 0 if files does not exist. """
		if not cls.exists():
			return 0
		return os.stat(cls.FILENAME).st_mtime
	def load(self):
		""" Loads data from file and returns Reader object.
		Returns None if file does not exist.
		"""
		if not self.exists():
			return None
		Log.debug('Loading savefile: {0}...'.format(self.FILENAME))
		with open(self.FILENAME, 'r') as f:
			data = f.read().split('\0')
		data = iter(data)
		return Reader(data)
	@contextlib.contextmanager
	def save(self, version):
		""" Should be used as context manager.
		Returns Writer object and starts with writing given version.
		Automatically closes file upon exiting context.
		"""
		try:
			with open(self.FILENAME, 'w') as f:
				yield Writer(f, version)
		except:
			self.unlink()
			raise
	def unlink(self):
		""" Removes save file if exists. """
		if not self.exists():
			return
		os.unlink(self.FILENAME)
