import os
import socket, time
import contextlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
try:
	import jsonpickle
except: # pragma: no cover
	jsonpickle = None

@contextlib.contextmanager
def CurrentDir(path):
	try:
		old_cwd = os.getcwd()
		os.chdir(str(path))
		yield
	finally:
		os.chdir(old_cwd)

def make_valid_filename(name):
	""" Converts given name to a valid filename. """
	return name.replace('/', '_')

def make_unique_filename(name):
	""" Creates filename that does not collide with existing files.
	May add random stuff between name and extension to make filename unique.
	Returns Path object.
	May return original name when fails to construct a unique name.
	"""
	name = Path(name)
	parent, stem, ext = name.parent, name.stem, name.suffix
	result = name
	for counter in range(0, 1000): # Very large number.
		if not result.exists():
			break
		result = parent/(stem + '.{0}'.format(counter) + ext)
	return result

class CrossHostFSMutex(object): # pragma: no cover -- TODO requires functional tests.
	""" Simple option to synchronize simultaneous actions on the same filesystem
	from different hosts.
	It uses file (should be accessible from every affected host) as a lock
	and stores hostname that holds the lock.
	Example usage:
	>>> lock = CrossHostFSMutex("path_to_lock_file")
	>>> lock.wait_lock(timeout=60)
	>>> with lock:
	...    do.action()
	"""
	def __init__(self, filename):
		self.filename = str(filename)
		self.hostname = socket.gethostname()
	def wait_lock(self, timeout=500):
		""" Tries to set lock for specified amount of seconds,
		if fails, then forces lock.
		"""
		for _ in range(timeout): # Timeout in seconds
			if self.try_lock():
				break
			time.sleep(1)
		else:
			self.force_lock()
		return True
	def _set(self):
		with open(self.filename, 'w') as f:
			f.write(self.hostname)
	def _get(self):
		try:
			with open(self.filename, 'r') as f:
				return f.read().strip()
		except:
			return None
	def try_lock(self):
		""" Tries to set the lock for the current hostname.
		Returns True if succeeded.
		"""
		if not os.path.exists(self.filename):
			self._set()
		if self._get() == self.hostname:
			# There is no direct way of communication between hosts by default,
			# so give it some time to sync FS operations at shared network location
			# and then ensure that we really have the lock.
			time.sleep(1)
			if self._get() == self.hostname:
				return True
			return False
		return False
	def force_lock(self):
		""" Forces lock for the current hostname. """
		self._set()
	def unlock(self):
		""" Removes lock file if the lock is being held by the current host. """
		if self._get() == self.hostname:
			try:
				os.unlink(str(self.filename))
			except:
				pass
	def __enter__(self):
		return self
	def __exit__(self, *args, **kwargs):
		self.unlock()

class SerializedEntity: # pragma: no cover -- TODO requires functional tests.
	def __init__(self, filename, current_version, entity_name='data', unlink=False, readable=False):
		self.filename = Path(filename)
		self.version = current_version
		self.entity_name = entity_name
		self.unlink = unlink
		self.readable = readable
		self.entity = None
	def load(self):
		if not self.filename.exists():
			return None
		data = self.filename.read_text()
		savedata = jsonpickle.decode(data, keys=True)
		if savedata['version'] > self.version:
			raise RuntimeError("Stored data version {0} is newer than currently supported {1}".format(savedata['version'], self.version))
		self.entity = savedata[self.entity_name]
		if self.unlink:
			os.unlink(str(self.filename))
		return self.entity
	def reset(self, new_value=None):
		self.entity = new_value
	def save(self, entity=None):
		if entity is None:
			entity = self.entity
		if entity is None:
			return
		savedata = {'version':self.version, self.entity_name:entity}
		if self.readable:
			data = jsonpickle.encode(savedata, indent=2, keys=True)
		else:
			data = jsonpickle.encode(savedata, keys=True)
		self.filename.write_text(data)
	def __enter__(self):
		self.load()
		return self
	def __exit__(self, *args, **kwargs):
		self.save()
