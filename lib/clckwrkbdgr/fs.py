import os
import contextlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

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

def make_unique_filename(name):
	""" Creates filename that does not collide with existing files.
	May add random stuff between name and extension to make filename unique.
	Returns Path object.
	May return original name when fails to construct a unique name.
	"""
	name = Path(name)
	parent, stem, ext = name.parent, name.stem, name.suffix
	result = name
	for counter in range(0, 1000): # Very large number.
		if not result.exists():
			break
		result = parent/(stem + '.{0}'.format(counter) + ext)
	return result
