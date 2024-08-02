import sys, os
import types
import itertools, functools
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

def chunks(seq, length, pad_value=None, pad=True):
	""" Splits sequence and yields chunks of specified length.
	Sequence can be any iterable. Type of chunks depends on type of sequences: list and strings are recognized, otherwise they will be tuples.
	If pad is True (by default), pads generated chunks to specified lengths with specified value.
	"""
	result_type = tuple
	if isinstance(seq, list):
		result_type = list
	elif isinstance(seq, str):
		pad_value = pad_value or ''
		result_type = ''.join
	if pad:
		result = six.moves.zip_longest(*[iter(seq)]*length, fillvalue=pad_value)
	else:
		it = iter(seq)
		result = iter(lambda: tuple(itertools.islice(it, length)), ())
	return map(result_type, result)

def is_integer(number):
	if isinstance(number, six.integer_types):
		return True
	try:
		return number.is_integer()
	except:
		return False

def import_module(module_spec, reload_module=False): # pragma: no cover -- TODO very specific functionality.
	""" Tries to load module by given spec:
	- module instance;
	- module name (available for direct import, e.g. in sys.path);
	- arbitrary file path (module name will be deducted from basename).
	If module is already loaded, does not reimport, unless reload_module=True.
	Returns loaded instance or None.
	Does not catch any import errors.
	"""
	if isinstance(module_spec, types.ModuleType):
		if sys.version_info < (3, 0):
			try:
				return reload(module_spec)
			except:
				module_spec = module_spec.__file__
		elif sys.version_info < (3, 4):
			import imp
			try:
				return imp.reload(module_spec)
			except:
				module_spec = module_spec.__file__
		else:
			import importlib
			try:
				return importlib.reload(module_spec)
			except ModuleNotFoundError:
				module_spec = module_spec.__file__

	module_filename = None
	module_name = module_spec
	if os.path.exists(module_spec):
		module_filename = module_spec
		module_name = os.path.basename(os.path.splitext(module_spec)[0])
		import re
		module_name = re.sub(r'\W|^(?=\d)','_', module_name)
	if reload_module and module_name in sys.modules:
		del sys.modules[module_name]

	if module_filename:
		try:
			import importlib.util
			spec = importlib.util.spec_from_file_location(module_name, module_filename)
			module_instance = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module_instance)
		except AttributeError:
			from importlib.machinery import SourceFileLoader
			module_instance = SourceFileLoader(module_name, module_filename).load_module()
		except ImportError:
			import imp
			module_instance = imp.load_source(module_name, module_filename)
	else:
		import importlib
		module_instance = importlib.import_module(module_name)
	if module_name not in sys.modules:
		sys.modules[module_name] = module_instance
	return module_instance

def load_entry_point(module_spec, function=None, reload_module=False): # pragma: no cover -- TODO very specific functionality.
	""" Loads entry point from given module and optional function.
	If module is a string, it may have format "file/name.py:function" or "module.name:function".
	In this case parsed function overrides argument.
	Otherwise, when function is not specified either way, first availabe function is picked.
	Returns pair (<module obj>, <function obj>)
	See also import_module()
	"""
	import inspect
	if isinstance(module_spec, six.string_types):
		try:
			try:
				import importlib.metadata as importlib_metadata
			except ImportError:
				import importlib_metadata
			entry_point = importlib_metadata.EntryPoint(name=None, group=None, value=module_spec)
			from collections import namedtuple
			entry_point = namedtuple('_EntryPoint', 'module_name attrs')(entry_point.module, tuple([entry_point.attr]))
		except: # Deprecated way.
			import pkg_resources
			entry_point = pkg_resources.EntryPoint.parse("name="+module_spec)
		module_spec = entry_point.module_name
		if entry_point.attrs:
			function = entry_point.attrs[0]
	module_spec = import_module(module_spec, reload_module=reload_module)
	if not isinstance(function, six.string_types):
		function = function.__name__
	if function:
		function = getattr(module_spec, function)
	else:
		all_functions = list(inspect.getmembers(module_spec, inspect.isfunction))
		function = all_functions[0][1]
	return module_spec, function

@contextlib.contextmanager
def ignore_warnings(): # pragma: no cover -- TODO very specific functionality.
	import warnings
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		yield
