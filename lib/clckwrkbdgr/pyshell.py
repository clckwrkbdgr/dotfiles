from __future__ import print_function, unicode_literals
import os, sys
import platform
import subprocess
try:
	subprocess.DEVNULL
except AttributeError: # pragma: no cover
	subprocess.DEVNULL = open(os.devnull, 'w')
import inspect
try: # pragma: no cover
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
import six
try:
	import termcolor
except ImportError: # pragma: no cover
	import clckwrkbdgr.dummy as termcolor

def is_collection(s):
	""" Returns True only if S is a true iterable (not string). """
	if isinstance(s, six.string_types):
		return False
	if s is None:
		return False
	try:
		iter(s)
		return True
	except TypeError:
		return False

def which(program, find_all=False): # pragma: no cover -- TODO separate module for utils
	EXECUTABLE_EXT = ['']
	if "PATHEXT" in os.environ:
		EXECUTABLE_EXT += os.environ["PATHEXT"].split(os.pathsep)

	result = []
	for path in [''] + os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		exe_file = Path(path)/program
		for ext in EXECUTABLE_EXT:
			fullpath = exe_file.with_suffix(ext) if ext else exe_file
			if fullpath.is_file() and os.access(str(fullpath), os.X_OK):
				if find_all:
					result.append(fullpath)
				else:
					return fullpath
	return result or None

def detach_process(): # pragma: no cover -- TODO some common cross-platform module
	import platform
	if not platform.system() == 'Windows':
		return 0
	CREATE_NEW_PROCESS_GROUP = 0x00000200  # note: could get it from subprocess
	DETACHED_PROCESS = 0x00000008          # 0x8 | 0x200 == 0x208
	return DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

if sys.stdout and sys.stdout.isatty() and platform.system() == 'Windows': # pragma: no cover -- TODO some common cross-platform module
	os.system("")
	os.system("color")

"""
Set $PYSHELL_DEBUG=1 to see debug traces.
Set $PYSHELL_DEBUG=0 or unset to stop.
"""

def DEBUG(*args, **kwargs): # pragma: no cover -- TODO logging
	is_on = os.environ.get('PYSHELL_DEBUG', None)
	if not is_on or is_on == '0':
		return
	if six.PY2: # pragma: py2 only
		caller = inspect.stack()[1][3]
	else: # pragma: py3 only
		caller = inspect.stack()[1].function
	kwargs['file'] = sys.stderr
	print('pyshell:DEBUG:{0}:'.format(caller), *args, **kwargs)

class ReturnCode(object):
	""" Wraps return code from shell command.
	Convertable to bool (True/False, logical expressions etc)
	and to int (including equality operators)
	"""
	def __init__(self, value=None):
		self.rc = value
		if self.rc is None:
			self.rc = 0
	def __repr__(self):
		return 'ReturnCode({0})'.format(repr(self.rc))
	def __str__(self):
		return str(self.rc)
	def __nonzero__(self): # pragma: no cover -- TODO py2 only
		return self.rc == 0
	def __bool__(self): # pragma: no cover -- TODO py3 only
		return self.rc == 0
	def __int__(self):
		return self.rc
	def __eq__(self, other):
		if other is True or other is False:
			return bool(self) == other
		return int(self) == other
	def __ne__(self, other):
		return not (self == other)

def expand_lists(values):
	""" If any argument in values sequence is a list, yields subvalues on the same level:
	[a, [b, c], d] => [a, b, c, d]
	"""
	for value in values:
		if is_collection(value):
			for subvalue in value:
				yield subvalue
		else:
			yield value

class PyShell(object):
	""" Main shell interface. """
	def __init__(self):
		self.rc = ReturnCode(0)
		self.old_pwd = os.getcwd()
	def ARGS(self):
		""" Returns all command-line args except the program name ($0).
		Equivalent of $@
		"""
		DEBUG("Retrieving $@: {0}".format(sys.argv[1:]))
		return tuple(sys.argv[1:])
	def ARG(self, index):
		""" Returns any command-line argument by index (${n})
		If there is no such argument, returns empty string.
		"""
		if index < 0 or len(sys.argv) <= index:
			DEBUG("Retrieving ARG {0}: <null>".format(index))
			return ''
		DEBUG("Retrieving ARG {0}: {1}".format(index, sys.argv[index]))
		return sys.argv[index]
	def _popen(self, *args, **kwargs):
		try:
			DEBUG("Popen({0})".format(
				', '.join(filter(lambda x:x, [
					', '.join(map(repr, args)),
					', '.join(['{0}={1}'.format(k, repr(v)) for k,v in kwargs.items()]),
					]))
				))
			return subprocess.Popen(*args, **kwargs)
		except OSError as e: # pragma: no cover -- TODO need some standard non-binary executable to test.
			DEBUG("Catched OSError: {0}".format(repr(e)))
			if e.winerror == 193: # "is not a valid Win32 application"
				DEBUG("Trying re-execute as shell...")
				return self._popen(*args, shell=True, **kwargs)
			raise
	def run(self, *args, **kwargs):
		""" Runs command specified by given args.
		Args are converted to strings and '~' is expanded if found.
		If some arg is a list, it is flattened.

		Kwargs are:
		- stdin=None
		- stdout='stdout'
		- stderr='stderr'
		- nohup=False

		Return ReturnCode object.

		By default stdout and stderr are tied with real streams.
		If stdout/stderr is str (actual type), stream is collected to string, decoded
		  and tail-stripped of whitespaces. Output is returned instead of usual RC.
		If stdout/stderr is None, output is ignored (>/dev/null).
		If stdout/stderr is a string, output is redirected to file.
		If stderr is 'stdout', it is joined to stdout (2>&1)
		In any other cases value is passed to subprocess call as-is.

		If nohup is True, control is returned back immediately, no RC or output is provided.
		"""
		stdin = kwargs.get('stdin', None)
		stdout = kwargs.get('stdout', 'stdout')
		stderr = kwargs.get('stderr', 'stderr')
		nohup = kwargs.get('nohup', False)

		DEBUG("Original args: {0}".format(args))
		args = expand_lists(args)
		args = map(str, args)
		args = map(os.path.expanduser, args)
		args = list(args)
		app_name = which(args[0])
		if app_name:
			args = [str(app_name)] + args[1:] # pragma: no cover -- TODO need some standard non-binary executable to test.
		DEBUG("Expanded args: {0}".format(args))

		kwargs = {}
		if stdin is not None:
			DEBUG("STDIN redirection is ON")
			kwargs['stdin'] = subprocess.PIPE
			if not isinstance(stdin, six.binary_type): # pragma: no cover -- py3 only
				DEBUG("Converting stdin content to bytes...")
				try:
					stdin = str(stdin).encode()
				except UnicodeError: # pragma: no cover
					stdin = str(stdin).encode('utf-8', 'replace')
		if stdout != 'stdout':
			DEBUG("STDOUT redirection is ON")
			if stdout is None:
				DEBUG("STDOUT >/dev/null")
				kwargs['stdout'] = subprocess.DEVNULL
			elif stdout == str:
				DEBUG("Capturing stdout to string.")
				kwargs['stdout'] = subprocess.PIPE
			elif isinstance(stdout, six.string_types): # pragma: no cover -- TODO to test
				DEBUG("Writing stdout to file: {0}".format(stdout))
				kwargs['stdout'] = open(stdout, 'w')
			else: # pragma: no cover -- TODO to test
				DEBUG("Writing stdout to {0}".format(repr(stdout)))
				kwargs['stdout'] = stdout
		if stderr != 'stderr':
			DEBUG("STDERR redirection is ON")
			if stderr is None:
				DEBUG("STDERR >/dev/null")
				kwargs['stderr'] = subprocess.DEVNULL
			elif stderr == 'stdout':
				DEBUG("STDER >&1")
				kwargs['stderr'] = subprocess.STDOUT
			elif isinstance(stderr, six.string_types): # pragma: no cover -- TODO to test
				DEBUG("Writing stderr to file: {0}".format(stderr))
				kwargs['stderr'] = open(stderr, 'w')
			else: # pragma: no cover -- TODO to test
				DEBUG("Writing stdout to {0}".format(repr(stderr)))
				kwargs['stderr'] = stderr
		if nohup:
			kwargs['stdin'] = subprocess.PIPE
			kwargs['stdout'] = subprocess.PIPE
			kwargs['stderr'] = subprocess.PIPE
			if platform.system() == 'Windows': # pragma: no cover -- TODO win only
				kwargs['creationflags'] = detach_process()
		try:
			p = self._popen(args, **kwargs)
			DEBUG('Started process with PID: {0}'.format(p.pid))
		except OSError as e: # pragma: no cover -- TODO need some standard non-binary executable to test.
			print(termcolor.colored(str(e) + ': ' + ' '.join(args), 'red'), file=sys.stderr) # TODO shlex.join ? Add and method into PyShell.
			return ReturnCode(-1)
		if nohup:
			DEBUG("Nohup, leaving.")
			return
		stdout, stderr = p.communicate(stdin)
		rc = p.wait()
		DEBUG("Process is done with RC: {0}".format(rc))
		DEBUG("STDOUT {0}, STDERR {1}".format(repr(stdout), repr(stderr)))
		self.rc = ReturnCode(rc)
		if (sys.stdout and sys.stdout.isatty()) or (sys.stderr and sys.stderr.isatty()): # pragma: no cover
			os.system("") # Hack to restore colors in Windows cmd console.
		if kwargs.get('stdout', None) == subprocess.PIPE:
			DEBUG("Decoding stdout...")
			stdout = stdout.rstrip()
			try:
				return stdout.decode()
			except UnicodeError: # pragma: no cover
				return stdout.decode('utf-8', 'replace')
		DEBUG("Done.")
		return self.rc
	def exit(self, value=None):
		""" Exits process.
		If value is not specified, uses RC of last command (or zero, if there were none).
		"""
		if value is not None:
			DEBUG("Exiting with RC: {0}".format(value))
			sys.exit(value)
		else:
			DEBUG("Exiting with RC from previous command: {0}".format(self.rc))
			sys.exit(int(self.rc))
	def __call__(self, *args, **kwargs):
		""" Shortcut to run shell command. """
		return self.run(*args, **kwargs)
	def __getitem__(self, name):
		""" Returns value of environment variable.
			sh['VAR'] === ${VAR}
		If variable is not set, returns empty string.
		"""
		DEBUG("Retrieving env: {0}".format(name))
		return os.environ.get(name, '')

	def cd(self, path):
		""" Changes current directory.
		Path is expanded automatically.
		"""
		if path == '-':
			DEBUG("CD to previous dir".format(path))
			cwd = os.getcwd()
			os.chdir(self.old_pwd)
			self.old_pwd = cwd
			return
		path = str(Path(path).expanduser())
		DEBUG("CD to {0}".format(path))
		self.old_pwd = os.getcwd()
		os.chdir(path)

def fail_report_excepthook(exc_type, exc_value, exc_traceback): # pragma: no cover
	if exc_type is KeyboardInterrupt:
		if sys.stdout and sys.stdout.isatty() and platform.system() == 'Windows': # pragma: no cover -- TODO
			os.system("")
			os.system("color")
		print(termcolor.colored('Interrupted', 'red'))
		return
	sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = fail_report_excepthook

sh = PyShell()

# Monkeypatching system exit so that it will return pyshell RC when no explicit RC is given by the caller.
original_exit = sys.exit
def _my_exit(*args): # pragma: no cover
	if not args:
		return original_exit(int(sh.rc))
	else:
		return original_exit(*args)
def _unmonkeypatch_sys_exit():
	sys.exit = original_exit
sys.exit = _my_exit
