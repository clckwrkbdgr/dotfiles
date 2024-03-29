from __future__ import division
import sys
import functools
try:
	import curses
except: # pragma: no cover
	curses = None
import six

@functools.total_ordering
class Key(object):
	""" Wrapper for getch'ed key.
	Unifies operations (initialization, comparison) for numeric value (key's integer value), string value (key's char):
	Key('A') == Key(65) == 'A' == 65
	"""
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
		return chr(self.value)

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
