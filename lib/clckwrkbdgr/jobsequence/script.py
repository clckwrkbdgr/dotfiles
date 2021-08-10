import os, sys, platform, stat
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

class Script(object): # pragma: no cover -- TODO need mocks.
	def __init__(self, name, shebang=None, rootdir=None):
		""" Creates script with specified name.
		Creates both path (by default is CWD) and script file.
		If shebang is specified, puts it in the first line.
		Makes script executable (depends on platform).
		"""
		rootdir = Path(rootdir or '.')
		rootdir.mkdir(exist_ok=True, parents=True)
		rootdir.resolve()
		self.filename = rootdir/name
		if self.filename.exists():
			raise RuntimeError("Script file already exists: {0}".format(self.filename))
		with self.filename.open('wb') as f:
			if shebang:
				f.write(shebang.encode('utf-8', 'replace') + b'\n')
		self._make_executable(self.filename)
	@staticmethod
	def _make_executable(filename):
		if platform.system() == 'Windows':
			return
		mode = filename.stat().st_mode
		filename.chmod(mode | stat.S_IXUSR)
	def append(self, line):
		""" Appends line to a file.
		Automatically puts linebreak if it is not present.
		"""
		with self.filename.open('a+') as f:
			f.write(line)
			if not line.endswith('\n'):
				f.write('\n')
	def __iadd__(self, line):
		""" Shortcut for append():
		script += "line"
		"""
		return self.append(line)
