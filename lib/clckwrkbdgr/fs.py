import os
import socket, time
import contextlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

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
