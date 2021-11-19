from . import cli, tui, gui
from ._base import *

def message(text): # pragma: no cover
	""" Displays text message and waits for user reaction.
	"""
	return _guess_backend().message(text)

def choice(items, prompt=None): # pragma: no cover
	""" Displays choice dialog.
	Items should be either strings or pair (key, item), where keys is also a string.
	Returns Choice object (index, key, text) if some item was selected,
	or None otherwise.
	"""
	return _guess_backend().choice(items, prompt=prompt)

def _guess_backend(): # pragma: no cover
	import sys
	if 'pythonw' in sys.executable:
		return gui
	if sys.stdout is None or not sys.stdout.isatty():
		return gui
	# TODO some way to detect TUI capabilities, like termcap
	return cli
