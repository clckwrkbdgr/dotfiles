import sys
import functools

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
