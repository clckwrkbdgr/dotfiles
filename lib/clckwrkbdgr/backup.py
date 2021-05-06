import os, tempfile
import contextlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

class Password(object):
	""" Encapsulates password so the actual value would not be present in stack traces.
	Real value is available only via str() within .disclosed() context manager.
	"""
	DUMMY = '*'*8
	def __init__(self, value):
		""" If value is None, essentially disables the password.
		bool(Password(None)) will return False and disclosed password will be empty string.
		"""
		self.__disclosed = False
		if isinstance(value, Password):
			self.__value = value.__value
			return
		if value is not None and not isinstance(value, str):
			raise TypeError('Expected password of type str, received {0}'.format(type(value)))
		self.__value = value
	def __bool__(self):
		return self.__value is not None
	__nonzero__ = __bool__
	@contextlib.contextmanager
	def disclosed(self):
		self.__disclosed = True
		try:
			yield
		finally:
			self.__disclosed = False
	def __str__(self):
		if self.__disclosed:
			return self.__value or ''
		return self.DUMMY
	def __repr__(self):
		return "Password({0})".format(self.DUMMY)

class PasswordArg(object):
	""" To prevent storing password as plain text variable
	up until command line is formed for the subprocess call.
	"""
	def __init__(self, password):
		self.password = password
	def __str__(self):
		return '-p{0}'.format(self.password)
	def __repr__(self):
		return repr(self.password)

class Config(object):
	""" Context for backup operation:
	- root: source directory for backup operations.
	  Tilde is recognized.
	  If path is not absolute, it is treated as relative to the current directory
	  (which should be directory of config file).
	  The only required parameter.
	- name: of the produced backup file.
	  By default will use basename of the root.
	- destinations: List of destination remote locations.
	  Environment variables and tilde are recognized.
	  By default produced backup will not be deployed anywhere.
	- tempdir: Temp dir for creating backup.
	  Should be absolute path. Tilde is recognized.
	  Default is system tempdir.
	- zip_path: Path to 7zip executable.
	  Should be absolute and resolved path.
	  By default will try to auto-detect installed 7zip in the system.
	- password: password to protect archive.
	  By default password is disabled.
	  Stored as protected Password object.
	  If password is a dict:
	  - { "file" : "<path to file with password>" }
	    Reads password from specified file.
		 Filename may contain environment variables and tilde.
	    File should contain a single line with optional EOL (it will be stripped automatically).
	- exclude: List of excluded directories and/or files.
	  May be wildcards.
	  By default all files are included.
	"""
	def __init__(self,
			root=None,
			name=None,
			destinations=None, tempdir=None, zip_path=None,
			password=None,
			exclude=None,
			): # pragma: no cover -- TODO accesses FS, needs proper mocks for FS and Path object.
		""" Creates context for backup operation.
		See main docstring for details on each parameter.
		"""
		self.root = Path(root).expanduser()
		self.name = name or self.root.name
		self.destinations = [Path(os.path.expandvars(location)).expanduser() for location in (destinations or [])]
		self.tempdir = Path(tempdir or tempfile.gettempdir()).expanduser()
		self.zip_path = Path(zip_path or r"C:\Program Files\7-Zip\7z.exe")
		self.exclude = list(exclude or [])
		if isinstance(password, dict):
			if 'file' in password:
				try:
					password = password['file']
					password = Path(os.path.expandvars(password)).expanduser().read_text()
					if password.endswith('\n'):
						password = password[:-1]
				except Exception as e:
					raise ValueError('Failed to read password file: {0}'.format(e))
			else:
				raise ValueError('Unknown password field configuration! Supported configurations are: plain string, {.file=<...>}')
		self.password = Password(password)
