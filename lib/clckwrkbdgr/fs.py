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
