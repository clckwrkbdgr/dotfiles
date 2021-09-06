from collections import namedtuple
from . import app
import curses

class TextScreen(app.MVC): # pragma: no cover -- TODO curses
	""" Displays visual notification on new screen
	and waits for any pressed key. If key is y/Y, returns RETURN_VALUE.
	If RETURN_VALUE is subclass of app.AppExit, raises exception instance instead.
	LINES is a list of message lines.
	Note: prompt "<press any key>" is included automatically on separate line.
	"""
	LINES = []
	RETURN_VALUE = None

	_full_redraw = True
	def _view(self, window):
		height, width = window.getmaxyx()
		lines = [line[:width] for line in self.LINES[:height-1]]
		lines.append("<press any key to continue>"[:width-1])
		for index, line in enumerate(lines):
			window.addstr(index, 0, line)
	def _control(self, ch):
		if issubclass(self.RETURN_VALUE, app.AppExit):
			raise self.RETURN_VALUE()
		return self.RETURN_VALUE

class Confirmation(app.ModalMVC): # pragma: no cover -- TODO curses
	""" Displays visual confirmation in the topmost line
	and waits for a pressed key.
	If key is y/Y, calls on_yes().
	Override MESSAGE value for confirmation message.
	Note: prompt "y/n" is included automatically.
	"""
	MESSAGE = None

	def on_yes(self):
		""" Override this function to performa actions
		when confirmation is successful.
		"""
		pass

	def __init__(self, *args, **kwargs):
		super(Confirmation, self).__init__(*args, **kwargs)
		self._responded = False
	def _view(self, window):
		_, width = window.getmaxyx()
		window.addstr(0, 0, " "*width)
		if not self._responded:
			prompt = " (y/n)"
			message = self.MESSAGE[:width-len(prompt)] + prompt
			window.addstr(0, 0, message)
	def _control(self, ch):
		if ch in [ord('y'), ord('Y')]:
			self.on_yes()
		if self._responded:
			return not None
		self._responded = True
		return None

class Menu(app.MVC): # pragma: no cover -- TODO curses
	""" Custom menu with items controlled by specific hot keys.
	Following options to override:
	- items(): list of Menu.Item(key, text)
	- KEYS_TO_CLOSE: keys that will immediately close menu and return to the mode specifed in on_close(). Default is ESC only.
	- on_close(): called when menu is simply closed. Should return new MVC.
	- on_item(item): called when item is selected.
	  Return value is treated as MVC mode: if None, continues with current menu,
	  otherwise starts new mode.
	WARNING: Scroll is not supported yet! Only items that fit into screen will be displayed.
	"""
	_full_redraw = True
	Item = namedtuple('MenuItem', 'key text data')

	KEYS_TO_CLOSE = [curses.ascii.ESC]
	def items(self):
		raise NotImplementedError
	def on_item(self, item):
		return None
	def on_close(self):
		return None

	def _view(self, window):
		height, width = window.getmaxyx()
		height -= 1 # For the top line.
		items = list(enumerate(self.items()))
		if len(items) >= height:
			items = items[:height-1] + [ (height-1, '[{0} more items do not fit...]'.format(len(items) - height + 1)) ]
		for row, item in items:
			line = "{0} - {1}".format(item.key, item.text)
			line = line[:width-1]
			window.addstr(1 + row, 0, line)
	def _control(self, ch):
		if any(ch == _ for _ in self.KEYS_TO_CLOSE):
			return self.on_close()
		for item in self.items():
			if ch == ord(item.key):
				return self.on_item(item)
		return None
