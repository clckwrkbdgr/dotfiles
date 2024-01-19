import os
import socket, time
import subprocess
import contextlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
try:
	import jsonpickle
except: # pragma: no cover
	jsonpickle = None

try:
	from ctypes.wintypes import MAX_PATH
except: # Fox Unix.
	MAX_PATH = os.pathconf('/', 'PC_NAME_MAX')

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

def make_unique_filename(name, max_path=MAX_PATH):
	""" Creates filename that does not collide with existing files.
	May add random stuff between name and extension to make filename unique.
	Returns Path object.
	May return original name when fails to construct a unique name.
	"""
	name = Path(name)
	parent, stem, ext = name.parent, name.stem, name.suffix
	if len(str(parent)) >= max_path:
		return name # Even dirname is longer than allowed, no sense to try to fit the basename part into limit, give up and let it fail.
	result = name
	if len(str(result)) > max_path:
		shorter_stem = stem[:len(stem) - (len(str(result)) - max_path)]
		result = Path(parent/(shorter_stem + ext))
	for counter in range(0, 1000): # Very large number.
		if not result.exists():
			break
		str_counter = '.{0}'.format(counter)
		result = parent/(stem + str_counter + ext)
		if len(str(result)) > max_path: # If too long, shrink the basename and apped counter as a suffix.
			result = Path(str(parent/stem)[:max_path - len(str_counter) - len(ext)] + str_counter + ext)
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
		self.filename.write_bytes(data.encode('utf-8', 'replace'))
	def __enter__(self):
		self.load()
		return self
	def __exit__(self, *args, **kwargs):
		self.save()

class LineReader:
	def __init__(self, filename):
		self.filename = Path(filename)
	def __str__(self):
		return str(self.filename)
	def __iter__(self):
		if not self.filename.exists():
			return
		for line in self.filename.read_text().splitlines():
			yield line

class FileWatcher(object):
	""" Performs action when file is modified. """
	def __init__(self, filename, action, quiet=False):
		""" Action is a function with no args.
		Filename is not required to exist.
		If quiet is True, caught exception will not be displayed.
		"""
		self.filename = str(filename)
		self.action = action
		self.quiet = quiet
		self._last_mtime = 0
		if os.path.exists(self.filename):
			self._last_mtime = os.stat(self.filename).st_mtime
	def check(self):
		""" If filename is updated since the last check,
		performs action and returns True.
		Otherwise returns False.
		All exceptions in action are caught and traceback is displayed (unless quiet mode is set),
		return value is still True in case of any exception.
		"""
		if not os.path.exists(self.filename):
			return False
		mtime = os.stat(self.filename).st_mtime
		if mtime <= self._last_mtime:
			return False
		try:
			self.action()
		except: # pragma: no cover
			import traceback
			traceback.print_exc()
		self._last_mtime = mtime
		return True

def disk_usage(path): # pragma: no cover -- TODO requires functional tests.
	""" Returns size in bytes for specified path. """
	output = subprocess.check_output(['du', '-s', str(path)])
	lines = output.decode().splitlines()
	if len(lines) != 1:
		raise RuntimeError('Expected a single line from `du`, received: {0}'.format(output))
	default_block_size = 512
	return int(lines[0].split(None, 1)[0]) * default_block_size

def find(root,
		exclude_names=None, exclude_dir_names=None, exclude_file_names=None,
		exclude_wildcards=None, exclude_dir_wildcards=None, exclude_file_wildcards=None,
		exclude_extensions=None,
		handle_dirs=False,
		):
	""" Iterates over file system (starting from given root).
	Yields Path objects (relative to the given root).
	If handle_dirs=True, also yields dir Paths. By default only files.
	If handle_dirs is callable(Path), it is called for each dir instead.

	Arguments exclude_* controls search:
	- exclude_dir_<kind> - excludes matching directories from stepping into;
	- exclude_file_<kind> - excludes matching files;
	- exclude_<kind> - excludes both dirs and files.
	Kinds of exclude matches:
	- exclude_wildcards - matches full (absolute) file path using fnmatch,
	  generic wildcards work too: '*.txt' etc;
	- exclude_extensions - matches extensions (files only), leading dot is optional;
	- exclude_names - matches exact base name.
	"""
	exclude_dir_names = list(map(str, (exclude_dir_names or []) + (exclude_names or [])))
	exclude_file_names = list(map(str, (exclude_file_names or []) + (exclude_names or [])))
	exclude_dir_wildcards = list(map(str, (exclude_dir_wildcards or []) + (exclude_wildcards or [])))
	exclude_file_wildcards = list(map(str, (exclude_file_wildcards or []) + (exclude_wildcards or [])))
	exclude_extensions = list(map(lambda _: (_ if _.startswith('.') else '.'+_), map(str, (exclude_extensions or []))))
	for root, dirs, files in os.walk(str(root)):
		root = Path(root)
		if callable(handle_dirs):
			handle_dirs(root)
		elif handle_dirs:
			yield root

		if exclude_dir_names:
			dirs[:] = [dirname for dirname in dirs if dirname not in exclude_dir_names]
		if exclude_dir_wildcards:
			dirs[:] = [dirname for dirname in dirs if not any((root/dirname).absolute().match(str(pattern)) for pattern in exclude_dir_wildcards)]

		for filename in files:
			filename = root/filename
			abs_filename = Path(os.path.abspath(str(filename))) # Path.absolute() does not work with pyfakefs.
			if exclude_file_wildcards and any(abs_filename.match(str(pattern)) for pattern in exclude_file_wildcards):
				continue
			if exclude_file_names and filename.name in exclude_file_names:
				continue
			if exclude_extensions and filename.suffix in exclude_extensions:
				continue
			yield filename
