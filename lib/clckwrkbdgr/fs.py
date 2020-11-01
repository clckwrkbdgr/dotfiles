import os
import contextlib

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
