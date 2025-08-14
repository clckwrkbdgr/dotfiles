import os
import contextlib
from clckwrkbdgr.math import Point, Size, Matrix
import vintage

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

class StreamReader:
	""" Provides read access to savefile (file-like object).
	Savefile version is available as field .version
	"""
	CHUNK_SIZE = 4096
	def __init__(self, f):
		""" Initializes reader over file and reads version.
		If f is an iterator, it should be over list of string values.
		"""
		self._buffer = ''
		self.stream = f
		self.version = self.read_int()
		self.meta_info = {}
	def set_meta_info(self, name, value): # pragma: no cover -- TODO
		""" Registers meta info for custom readers (see read()). """
		self.meta_info[name] = value
	def get_meta_info(self, name): # pragma: no cover -- TODO
		""" Should be used from within custom reader to get associated meta info
		(see read()).
		"""
		return self.meta_info[name]
	def read_raw(self):
		""" Reads raw data unit. """
		if not self._buffer:
			self._buffer = self.stream.read(self.CHUNK_SIZE)
			assert self._buffer
		data = None
		while True:
			try:
				data, self._buffer = self._buffer.split('\0', 1)
				break
			except ValueError:
				new_chunk = self.stream.read(self.CHUNK_SIZE)
				if not new_chunk:
					data = self._buffer
					break
				self._buffer += new_chunk
		return data
	def read(self, custom_type=None, optional=False):
		""" Reads current value from stream.
		If custom_type is specified:
		- if it has class method .load(<reader>), it is used instead;
		- otherwise value is cast to that type directly.
		Custom loaders should create and return fully-prepared objects.
		If any external data is needed for deserialization, it can be
		registered via set_meta_info().

		If optional is True, first reads option flag (bool).
		If flag is False, skips reading item and returns None.
		Otherwise reads full item.
		"""
		if optional:
			if not self.read_bool():
				return None
		if custom_type and hasattr(custom_type, 'load'):
			return custom_type.load(self)
		value = self.read_raw()
		if custom_type:
			value = custom_type(value)
		return value
	def read_int(self):
		""" Reads value as integer. """
		return int(self.read())
	def read_str(self):
		""" Reads value as string.
		Recognizes None.
		"""
		value = self.read()
		return value if value != 'None' else None
	def read_bool(self):
		""" Reads value as bool. """
		value = self.read()
		return value == '1'
	def read_point(self):
		""" Reads two integer as point coords. """
		return Point(self.read_int(), self.read_int())
	def read_size(self):
		""" Reads two integer as size dims. """
		return Size(self.read_int(), self.read_int())
	def read_list(self, element_type=None):
		""" Reads list of elements: int len.
		If element_type is specified, its load() is used.
		Otherwise it is considered built-in type.
		"""
		count = self.read_int()
		result = []
		for _ in range(count):
			result.append(self.read(element_type))
		return result
	def read_matrix(self, element_type=None):
		""" Reads matrix of elements: Size.
		If element_type is specified, its load() is used.
		Otherwise it is considered built-in type.
		"""
		size = self.read_size()
		result = Matrix(size, None)
		for _ in range(size.width * size.height):
			result.data[_] = self.read(element_type)
		return result

class Reader(StreamReader): # pragma: no cover -- deprecated
	def __init__(self, f):
		self._buffer = ''
		if hasattr(f, 'read'):
			self.stream = iter(f.read().split('\0'))
		else:
			self.stream = f
		self.version = self.read_int()
		self.meta_info = {}
	def read_raw(self):
		return next(self.stream)

class Writer:
	""" Provides read access to savefile (file-like object).
	Savefile version is available as field .version
	"""
	def __init__(self, f, version):
		""" Initializes writer over stream and writes version.
		"""
		self.version = version
		self.f = f
		self.f.write(str(version))
	def write(self, item, optional=False):
		""" Writes string representation of item to the file.
		Several built-in types are recognized as special serialization.
		Additional, if item has method save(<writer>), it is used instead.

		If optional is True, detects if item is None and writes flag False.
		Otherwise, is item is not None, writes flag True and the serializes item.
		"""
		if optional:
			if item is None:
				return self.write_bool(False)
			self.write_bool(True)
		if hasattr(item, 'save'):
			return item.save(self)
		if isinstance(item, bool):
			return self.write_bool(item)
		if isinstance(item, Point):
			return self.write_point(item)
		if isinstance(item, Size):
			return self.write_size(item)
		if isinstance(item, list):
			return self.write_list(item)
		if isinstance(item, Matrix):
			return self.write_matrix(item)
		return self.write_raw(item)
	def write_raw(self, item):
		""" Writer RAW string representation of the value. """
		self.f.write('\0')
		self.f.write(str(item))
	def write_bool(self, bool_value):
		""" Booleans are converted to integer first. """
		return self.write_raw(int(bool_value))
	def write_point(self, point):
		""" Points are serialized as a pair of coordinates. """
		self.write_raw(point.x)
		self.write_raw(point.y)
	def write_size(self, size):
		""" Size are serialized as a pair of dimensions. """
		self.write_raw(size.width)
		self.write_raw(size.height)
	def write_list(self, item_list):
		""" Writes size of the list and then each item consequently. """
		self.write(len(item_list))
		for item in item_list:
			self.write(item)
	def write_matrix(self, matrix):
		""" Writes size of the matrix and then each item consequently. """
		self.write(matrix.size)
		for cell in matrix.data:
			self.write(cell)

class Savefile:
	""" Versioned save file to serialize/deserialize objects.
	Provides wrapper interface for Reader/Writer objects.

	Default implementation is a text file: set of string values separated by NULL character.

	See load()/save()
	"""
	def __init__(self, filename):
		self.filename = str(filename)
	def exists(self):
		""" Should return True if file exists. """
		return os.path.exists(self.filename)
	def last_save_time(self):
		""" Should return mtime of the existing file, or 0 if files does not exist. """
		if not self.exists():
			return 0
		return os.stat(self.filename).st_mtime
	@vintage.deprecated("Use Savefile.get_reader()")
	def load(self): # pragma: no cover -- deprecated
		""" Loads data from file and returns LegacyReader object.
		Returns None if file does not exist.
		"""
		if not self.exists():
			return None
		with open(self.filename, 'r') as f:
			return Reader(f)
	@contextlib.contextmanager
	def get_reader(self):
		""" Should be used as context manager.
		Yields Reader object, ready for streaming.
		Yields None if file does not exist.
		"""
		if not self.exists():
			yield None
			return
		with open(self.filename, 'r') as f:
			yield StreamReader(f)
	@contextlib.contextmanager
	def save(self, version):
		""" Should be used as context manager.
		Returns Writer object and starts with writing given version.
		Automatically closes file upon exiting context.
		"""
		try:
			with open(self.filename, 'w') as f:
				writer = Writer(f, version)
				yield writer
				# Otherwise if stream ends with a series of empty values
				# separated by \x00, that tail would be cut off
				# on the next loading.
				# File should be ended with something non-NULL.
				writer.write('EOF')
		except:
			self.unlink()
			raise
	def unlink(self):
		""" Removes save file if exists. """
		if not self.exists():
			return
		os.unlink(self.filename)
