import sys
import functools
import contextlib
import six

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
				bin_stdout = io.open(sys.stdout.fileno(), 'wb')
				yield bin_stdout
			else:
				yield sys.stdout
		else:
			f = open(filename, mode)
			yield f
	finally:
		if f:
			f.close()

def quote_string(string, beginquote='"', endquote=None):
	""" If endquote is not specified, the beginquote value is used for it. """
	if endquote is None:
		endquote = beginquote
	if beginquote in string:
		string = string.replace(beginquote, '\\'+beginquote)
	if endquote != beginquote and endquote in string:
		string = string.replace(endquote, '\\'+endquote)
	return beginquote + string + endquote

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

def get_type_by_name(type_name, frame_correction=0):
	""" Returns type object from given name.
	Recognizes:
	- builtin types (str, int etc).
	- types from current (caller) module.
	  Set frame correction in case when this function is called non-directly
	  (+1 for each level of indirection).
	- fully-quialified type names (with module). Module must be imported in caller's namespace.
	Otherwise raises RuntimeError.
	"""
	try:
		if six.PY2: # pragma: no cover -- Py2 only.
			return __builtins__[type_name]
		else: # pragma: no cover -- Py3 only.
			import builtins
			return getattr(builtins, type_name)
	except (KeyError, AttributeError):
		import inspect
		try:
			caller = inspect.currentframe().f_back
			for _ in range(frame_correction):
				caller = caller.f_back
			parts = type_name.split('.')
			type_obj = caller.f_globals[parts.pop(0)]
			while parts:
				type_obj = getattr(type_obj, parts.pop(0))
			if six.PY2: # pragma: no cover -- Py2 only.
				import types
				type_of_type = (types.TypeType, types.ClassType)
			else: # pragma: no cover -- Py3 only.
				type_of_type = type
			if isinstance(type_obj, type_of_type):
				return type_obj
		except KeyError:
			pass
	raise RuntimeError("Unknown type or not a type: {0}".format(type_name))

class ClassField:
	""" Internal implementation of classfield functionality. """
	def __init__(self, name, default_value):
		self.name = name
		self.default_value = default_value
	def __call__(self, obj):
		if hasattr(obj, self.name):
			return getattr(obj, self.name)
		return self.default_value

def classfield(name, default_value):
	""" Defines property for accessing class-level field in ancestor classes
	in a hierarchy of objects with similar behavior but different characteristics.

	If ancestor class does not define property with such name, default value will be returned.

	Example:
	class Base:
		name = classfield('_name', 'default')
	class Custom(Base):
		_name = 'custom'
	class Default(Base):
		pass
	Custom().name == 'custom'
	Default().name == 'default'
	"""
	return property(ClassField(name, default_value))
