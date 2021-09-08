from collections import namedtuple
import curses, curses.ascii
import clckwrkbdgr.text
from . import app, Key

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
	- prompt(): text for the top line. By default is empty.
	- items(): list of Menu.Item(key, text)
	- COLUMNS: number of columns to display. Default is 1.
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
	COLUMNS = 1
	def items(self):
		raise NotImplementedError
	def on_item(self, item):
		return None
	def on_close(self):
		return None
	def prompt(self):
		return ""

	def _view(self, window):
		height, width = window.getmaxyx()
		window.addstr(0, 0, str(self.prompt())[:width])

		height -= 1 # For the top line.
		column_width = width // self.COLUMNS
		allowed_items = height * self.COLUMNS
		items = list(enumerate(self.items()))
		if len(items) >= allowed_items:
			items = items[:allowed_items-1] + [ (allowed_items-1, '[{0} more items do not fit...]'.format(len(items) - allowed_items + 1)) ]
		for index, item in items:
			line = "{0} - {1}".format(Key(item.key), item.text)
			line = line[:column_width-1]
			column_start = (index // height) * column_width
			row = index % height
			window.addstr(1 + row, column_start, line)
	def _control(self, ch):
		if any(ch == _ for _ in self.KEYS_TO_CLOSE):
			return self.on_close()
		for item in self.items():
			if ch == item.key:
				return self.on_item(item)
		return None

class MessageLineOverlay(app.OverlayMVC): # pragma: no cover -- TODO curses
	""" Overlay that provides message line (the topmost line).
	Messages are condensed if possible.
	Override MORE_KEY (tui.Key) to specify key that advances pending messages. Default is Space.
	Override get_new_messages() to produce actual messages.
	"""
	MORE_KEY = Key(' ')

	def __init__(self, *args, **kwargs):
		super(MessageLineOverlay, self).__init__(*args, **kwargs)
		self._messages = []
		self._to_remove = None
		self._top_message = None
	def add_message(self, text):
		""" Adds new message. """
		self._messages.append(str(line))
	def _view(self, window):
		self._messages.extend(map(str, self.get_new_messages()))

		_, width = window.getmaxyx()
		self._to_remove, self._top_message = clckwrkbdgr.text.wrap_lines(
				self._messages,
				width=width, ellipsis=self.MORE_KEY.name(),
				force_ellipsis=self.force_ellipsis(),
				rjust_ellipsis=True,
				)

		if not self._messages:
			return
		window.addstr(0, 0, " "*width)
		window.addstr(0, 0, self._top_message)
	def _control(self, ch):
		if not self._messages:
			return not None
		if not self._to_remove:
			self._messages.clear()
			return not None
		if ch != self.MORE_KEY:
			return None
		if self._to_remove > 0:
			self._messages = self._messages[self._to_remove:]
		else:
			self._messages[0] = self._messages[0][-self._to_remove:]
		return None

	def get_new_messages(self):
		""" Override this method to get new messages, e.g. from self.data.
		May be a generator.
		"""
		return []
	def force_ellipsis(self):
		""" Override this method to return True when ellipsis ("more") should be forced regardless of pending messages.
		"""
		return False
