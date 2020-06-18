import sys
import six

""" Custom 'moves' extensions for 'six' module.
Just import this module ('_six') to install custom moves to global namespace 'six.moves.clckwrkbdgr.*':
Also handles all available backports (like shutil_get_terminal_size, functools_lru_cache),
again automatically just by importing this module.
"""

six.add_move(six.MovedModule('clckwrkbdgr', 'clckwrkbdgr._six', 'clckwrkbdgr._six'))


def _backport(module, backport_name): # pragma: no cover -- TODO need some way to test this.
	""" Applies backport patch for the module.
	`backport_name` should be in form `<module_name>_<function_name>,
	e.g.: shutil_get_terminal_size.
	If `shutil.get_terminal_size` is not defined,
	it tries to import `get_terminal_size` from `backports.shutil_get_terminal_size` into `shutil` module.
	"""
	backport_module_name, function_name = backport_name.split('_', 1)
	if hasattr(module, function_name):
		return
	if module.__name__ in sys.modules and hasattr(sys.modules[module.__name__], function_name):
		return
	backport_module = __import__('backports.' + backport_name, fromlist=(b'',))
	function = getattr(backport_module, function_name)
	setattr(module, function_name, function)
	if module.__name__ in sys.modules:
		setattr(sys.modules[module.__name__], function_name, function)

import shutil
try:
	_backport(shutil, 'shutil_get_terminal_size')
except ImportError: # pragma: no cover
	shutil.get_terminal_size = lambda: (80, 24)
import functools
try:
	_backport(functools, 'functools_lru_cache')
except ImportError: # pragma: no cover
	functools.lru_cache = lambda *args, **kwargs: (lambda func: func)

