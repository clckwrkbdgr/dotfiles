import sys
import functools
import contextlib

def convert_to_exit_code(value):
	""" Converts value to a valid exit code parameter for sys.exit()
	Conversion rules:
	1. None is considered success, i.e. 0
	2. bool values are not converted to integer directly: True -> 0, False -> 1
	3. Integer values are returned as-is.
	4. Any other value is converted to bool() first (see #2).
	"""
	if value is None:
		return 0
	if value is True:
		return 0
	if value is False:
		return 1
	try:
		return value + 0
	except:
		value = bool(value)
		return 0 if value else 1

def returns_exit_code(function):
	""" Converts return value of the function to a valid exit code parameter for sys.exit()
	See convert_to_exit_code() for details.
	"""
	@functools.wraps(function)
	def _wrapper(*args, **kwargs):
		return_value = function(*args, **kwargs)
		exit_code = convert_to_exit_code(return_value)
		return exit_code
	return _wrapper

def exits_with_return_value(function):
	""" Converts return value of the function to a valid exit code parameter for sys.exit()
	and the calls sys.exit() instead of returning value.
	Useful with click.commands.
	See convert_to_exit_code() for details.
	"""
	@functools.wraps(function)
	def _wrapper(*args, **kwargs):
		return_value = function(*args, **kwargs)
		exit_code = convert_to_exit_code(return_value)
		sys.exit(exit_code)
	return _wrapper

@contextlib.contextmanager
def fileinput(filename, mode=None): # pragma: no cover -- TODO uses sys.stdin, needs mocks.
	""" Creates context for reading specified file.
	If filename is None, empty or '-', reads stdin instead.
	If mode is binary (default is text) and stdin is used, re-opens stdin in binary mode.
	"""
	f = None
	try:
		if not filename or filename == '-':
			if 'b' in mode:
				import io
				bin_stdin = io.open(sys.stdin.fileno(), 'rb')
				yield bin_stdin
			else:
				yield sys.stdin
		else:
			f = open(filename, mode)
			yield f
	finally:
		if f:
			f.close()

@contextlib.contextmanager
def fileoutput(filename, mode=None): # pragma: no cover -- TODO uses sys.stdout, needs mocks
	""" Creates context for writing to specified file.
	If filename is None, empty or '-', writes to stdout instead.
	If mode is binary (default is text) and stdout is used, re-opens stdout in binary mode.
	"""
	f = None
	try:
		if not filename or filename == '-':
			if 'b' in mode:
				import io
				bin_stdout = io.open(sys.stdin.fileno(), 'wb')
				yield bin_stdout
			else:
				yield sys.stdout
		else:
			f = open(filename, mode)
			yield f
	finally:
		if f:
			f.close()

def unquote_string(string, fix_unicode_escape=False):
	string = string.strip()
	if string.startswith('"') and string.endswith('"'):
		string = string[1:-1]
	if string.startswith("'") and string.endswith("'"):
		string = string[1:-1]
	# Apparently 'unicode_escape' returns string with corrupted utf-8 encoding.
	if fix_unicode_escape: # pragma: no cover -- TODO what's this for? Came from xfce-leds while reading ini.
		string = bytes(string, "utf-8").decode('unicode_escape').encode("latin1").decode("utf-8")
	return string
