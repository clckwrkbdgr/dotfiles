from __future__ import division
import sys
import functools
from .. import utils
from collections import namedtuple
try:
	import curses
	import curses.ascii
except: # pragma: no cover
	curses = None
import six

@functools.total_ordering
class Key(object):
	""" Wrapper for getch'ed key.
	Unifies operations (initialization, comparison) for numeric value (key's integer value), string value (key's char):
	Key('A') == Key(65) == 'A' == 65
	"""
	ESCAPE = curses.ascii.ESC

	def __init__(self, value):
		if isinstance(value, Key):
			self.value = value.value
		elif isinstance(value, six.string_types):
			self.value = ord(value)
		else:
			self.value = int(value)
	def __hash__(self):
		return hash(self.value)
	def __str__(self): # pragma: no cover
		return chr(self.value)
	def __repr__(self): # pragma: no cover
		return 'Key({0} {1})'.format(self.value, repr(chr(self.value)))
	def __lt__(self, other):
		other = Key(other)
		return self.value < other.value
	def __eq__(self, other):
		other = Key(other)
		return self.value == other.value
	def name(self): # pragma: no cover -- TODO
		""" Returns human-readable name. """
		if self.value == ord(' '):
			return 'space'
		if self.value == curses.ascii.ESC:
			return 'escape'
		return chr(self.value)

class Keymapping: # pragma: no cover -- TODO
	""" Keybingings registry.

	Bind callables to keys:

	keys = Keymapping()
	@keys.bind('a')
	def perform_a():
		...
	callback = keys.get('a')
	callback()
	"""
	Keybinding = namedtuple('Keybinding', 'key callback param help')

	def __init__(self):
		self.keybindings = {}
		self.multikeybindings = {}
	def map(self, key, value, help=None):
		""" Maps key (or several keys) to a value.
		If value is callable, it is called with argument of actual key name (useful in case of multikeys) and its result is used as an actual value instead.
		Optional help description can be specified.
		"""
		if utils.is_collection(key):
			keys = tuple(Key(subkey) for subkey in key)
			actual_value = value
			if callable(value):
				def _resolved_value(_pressed_key, _keys=keys):
					return value(_keys[_keys.index(Key(_pressed_key))])
				actual_value = _resolved_value
			self.multikeybindings[keys] = self.Keybinding(keys, None, actual_value, help)
		else:
			self.keybindings[Key(key)] = self.Keybinding(key, None, value, help)
	def bind(self, key, param=None, help=None):
		""" Serves as decorator and binds key (or several keys) to action callback.
		Optional param may be passed to callback.
		If param is callable, it is called with argument of actual key name (useful in case of multikeys) and its result is used as an actual param instead.
		Optional help description can be specified. If not, docstring for the callback is used as help (if present).
		"""
		_help_description = help
		def _actual(f, help_description=_help_description):
			if not help_description:
				help_description = f.__doc__.strip()
			if utils.is_collection(key):
				keys = tuple(Key(subkey) for subkey in key)
				actual_param = param
				if callable(param):
					def _resolved_param(_pressed_key, _keys=keys):
						return param(_keys[_keys.index(Key(_pressed_key))])
					actual_param = _resolved_param
				self.multikeybindings[keys] = self.Keybinding(keys, f, actual_param, help_description)
			else:
				self.keybindings[Key(key)] = self.Keybinding(key, f, param, help_description)
			return f
		return _actual
	def get(self, key, bind_self=None):
		""" Returns bound value or callback for given key.
		If param is defined for the key, processes it automatically
		and returns closure with param bound as the last argument:
		keybinding.callback(..., param) -> callback(...)
		If bind_self is given, considers callback a method
		and binds it to the given instance.
		"""
		binding = self.keybindings.get(key)
		if not binding:
			binding = next((
				_binding for keys, _binding in self.multikeybindings.items()
				if key in keys
				), None)
		if not binding:
			return None
		if not binding.callback:
			param = binding.param
			if callable(param):
				param = param(key)
			return param
		callback = binding.callback
		if bind_self:
			callback = callback.__get__(bind_self, type(bind_self))
		param = binding.param
		if not param:
			return callback
		if callable(param):
			param = param(key)
		def _bound_param(*args):
			args = args + (param,)
			return callback(*args)
		return _bound_param
	def list_all(self):
		""" Returns sorted list of all keybindings (multikeys first). """
		return sorted(self.multikeybindings.items()) + sorted(self.keybindings.items())

class Curses(object):
	def __init__(self): # pragma: no cover -- TODO
		self.window = None
		self._nodelay = False
	def __enter__(self): # pragma: no cover -- TODO Mostly repeats curses.wrapper - original wrapper has no context manager option.
		self.window = curses.initscr()
		curses.noecho()
		curses.cbreak()
		self.window.keypad(1)
		try:
			curses.start_color()
		except:
			pass
		# Custom actions, not from curses.wrapper
		curses.curs_set(0)
		return self
	def __exit__(self, *_targs): # pragma: no cover -- TODO Mostly repeats curses.wrapper - original wrapper has no context manager option.
		self.window.keypad(0)
		curses.echo()
		curses.nocbreak()
		curses.endwin()
	
	def get_keypress(self, nodelay=False, timeout=100): # pragma: no cover -- TODO
		""" Returns Key object for the pressed key.
		Waits for keypress, unless nodelay is specified - in that case
		returns key immediately (after specified timeout msec)
		or None, if no keys are pressed.
		"""
		nodelay = bool(nodelay)
		if self._nodelay != nodelay:
			if nodelay:
				self.window.nodelay(1)
				self.window.timeout(timeout)
			else:
				self.window.nodelay(0)
				self.window.timeout(-1)
			self._nodelay = nodelay
		ch = self.window.getch()
		if ch == -1:
			return None
		return Key(ch)
	def get_control(self, keymapping, nodelay=False, timeout=100, bind_self=None, callback_args=None, callback_kwargs=None): # pragma: no cover -- TODO
		""" Returns mapped object from keymapping for the pressed key
		or None in case of unknown key (or no keypress in the nodelay mode).
		See get_keypress and Keymapping.get for other details.
		Callback will be detected and executed automatically.
		If callback_args and/or callback_kwargs are given and callback is bound,
		they will be passed as args/kwargs to the callback.
		"""
		key = self.get_keypress(nodelay=nodelay, timeout=timeout)
		if key is None:
			return None
		control = keymapping.get(key, bind_self=bind_self)
		if callable(control):
			callback_args = callback_args or []
			callback_kwargs = callback_kwargs or {}
			control = control(*callback_args, **callback_kwargs)
		return control

class ExceptionScreen(object):
	""" Context manager that captures exceptions and displays traceback in window overlay,
	prompting to press a key to either exit immediately (quit_key, raises sys.exit) or proceed (any other).
	"""
	def __init__(self, window, quit_key='Q', prompt='[Press <Q> to quit, any other key to continue]'): # pragma: no cover
		self.window = window
		self.quit_key = Key(quit_key)
		self.prompt = prompt
	def __enter__(self): # pragma: no cover
		return self
	@staticmethod
	def _fit_into_bounds(text, width, height):
		""" Split text into lines and returns parts fitting into specified bounds. """
		lines = [line.replace('\t', '  ')[:width] for line in text.splitlines()]
		if len(lines) > height:
			top_part = bottom_part = height // 2
			top_part -= 1
			while top_part + 1 + bottom_part < height:
				top_part += 1
			lines = lines[:top_part] + ['[...]'] + lines[-bottom_part:]
		return lines
	def __exit__(self, exc_type, exc_value, exc_traceback): # pragma: no cover -- TUI
		if exc_type is None:
			return
		import traceback
		height, width = self.window.getmaxyx()
		lines = self._fit_into_bounds(traceback.format_exc(), width, height - 1)
		lines += [self.prompt[:width - 1]] # Skip the very bottom-right character because it will move cursor and trigger curses out-of-screen exception.

		self.window.clear()
		for row, line in enumerate(lines):
			self.window.addstr(row, 0, line)
		self.window.refresh()
		if self.window.getch() == self.quit_key:
			sys.exit()
		self.window.clear()
		return True # Ignore exception and proceed.
