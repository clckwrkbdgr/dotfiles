import sys
import functools

def convert_to_exit_code(value):
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
	@functools.wraps(function)
	def _wrapper(*args, **kwargs):
		return_value = function(*args, **kwargs)
		exit_code = convert_to_exit_code(return_value)
		return exit_code
	return _wrapper
