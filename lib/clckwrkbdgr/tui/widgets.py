from collections import namedtuple
try:
	ClassType = (type, types.ClassType)
except: # pragma: no cover
	ClassType = type
try:
	import curses, curses.ascii
except: # pragma: no cover
	from ..collections import dotdict
	curses = dotdict()
	curses.ascii = dotdict()
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
	def on_close(self):
		return self.RETURN_VALUE

	_full_redraw = True
	def _view(self, window):
		height, width = window.getmaxyx()
		lines = [line[:width] for line in self.LINES[:height-1]]
		lines.append("<press any key to continue>"[:width-1])
		for index, line in enumerate(lines):
			window.addstr(index, 0, line)
	def _control(self, ch):
		return_value = self.on_close()
		if isinstance(return_value, ClassType) and issubclass(return_value, app.AppExit):
			raise return_value()
		return return_value

class Prompt(app.ModalMVC): # pragma: no cover -- TODO curses
	""" Displays visual prompt in the topmost line,
	waits for a key and calls on_key(key).
	Method on_choice should return new mode or None (following ModalMVC behavior).
	Method choices() should return all allowed keys as a list.
	Override MESSAGE value or prompt() for the prompt message.
	Default prompt is MESSAGE.
	Override KEYS_TO_CLOSE to immediately close menu and return to the main mode. Default is ESC only.
	Note: allowed keys are included automatically into prompt.
	"""
	_full_redraw = False

	MESSAGE = None
	KEYS_TO_CLOSE = [curses.ascii.ESC]

	def choices(self):
		return []
	def on_choice(self, key):
		return not None
	def prompt(self):
		return self.MESSAGE

	def __init__(self, *args, **kwargs):
		super(Prompt, self).__init__(*args, **kwargs)
		self._responded = False
	@staticmethod
	def _prompt_from_choices(choices):
		choices = list(map(Key, choices))
		if len(choices) == 1:
			return choices[0].name()
		if len(choices) == 2 and abs(choices[0].value - choices[1].value) > 1:
			return ",".join(c.name() for c in choices)
		choices = sorted(choices, key=lambda k:k.value)
		prev = None
		ranged = []
		for choice in choices:
			if prev and abs(prev.value - choice.value) == 1:
				ranged.append('-')
			else:
				if prev and ranged and ranged[-1] == '-':
					ranged.append(prev.name())
				ranged.append(choice.name())
			prev = choice
		if prev and ranged and ranged[-1] == '-':
			ranged.append(prev.name())
		squeezed = []
		for choice in ranged:
			if choice == '-' and squeezed and choice == squeezed[-1]:
				continue
			else:
				if len(squeezed) >= 2 and squeezed[-2] == '-':
					squeezed.append(',')
				elif squeezed and squeezed[-1] != '-' and choice != '-':
					squeezed.append(',')
				squeezed.append(choice)
		return ''.join(squeezed)
	def _view(self, window):
		_, width = window.getmaxyx()
		window.addstr(0, 0, " "*width)
		if not self._responded:
			prompt = " (" + self._prompt_from_choices(self.choices()) + ")"
			message = self.prompt()[:width-len(prompt)] + prompt
			window.addstr(0, 0, message)
	def _control(self, ch):
		if any(ch == _ for _ in self.KEYS_TO_CLOSE):
			return self.actual_mode
		if self._responded:
			return self._responded
		if ch in map(Key, self.choices()):
			return self.on_choice(ch)
		return self.actual_mode

class Confirmation(Prompt): # pragma: no cover -- TODO curses
	""" Displays visual confirmation in the topmost line
	and waits for a pressed key.
	If key is y/Y, calls on_yes().
	Override MESSAGE value for confirmation message.
	Note: prompt "y/n" is included automatically.
	"""

	def on_yes(self):
		""" Override this function to performa actions
		when confirmation is successful.
		"""
		pass

	def choices(self):
		return ["y", "n"]
	def on_choice(self, key):
		if key in [ord('y'), ord('Y')]:
			self.on_yes()
		return self.actual_mode

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
			return None
		if not self._to_remove:
			del self._messages[:]
			return None
		if ch != self.MORE_KEY:
			return self
		if self._to_remove > 0:
			self._messages = self._messages[self._to_remove:]
		else:
			self._messages[0] = self._messages[0][-self._to_remove:]
		return self

	def get_new_messages(self):
		""" Override this method to get new messages, e.g. from self.data.
		May be a generator.
		"""
		return []
	def force_ellipsis(self):
		""" Override this method to return True when ellipsis ("more") should be forced regardless of pending messages.
		"""
		return False

class StatusLine(app.OverlayMVC): # pragma: no cover -- TODO curses
	""" Status line with sections.
	Takes the bottommost line.
	Override list of SECTIONS (see LabeledSection).
	Optional fixed CORNER element may be displayed in bottom-right corner.
	Sections are separated with SEPARATOR (default is two spaces).

	LabeledSection ("<label>:<value>"):
	- width - is the width of value. Section will be aligned to that width (value is right-justified).
	- getter - function that received mode's data and should return:
	  - (not None) Displayed value;
	  - None if section should be skipped.
	"""
	LabeledSection = namedtuple('StatusLineLabeledSection', 'label width getter')
	SECTIONS = []
	SEPARATOR = "  "
	CORNER = ""
	def _control(self, _): return None
	def _view(self, window):
		status = ""
		for name, width, getter in self.SECTIONS:
			value = getter(self.data)
			if status:
				status += self.SEPARATOR
			if value is None:
				status += " "*(len(name) + 2 + width)
			else:
				status += "{0}:{1}".format(name, str(value)[:width].rjust(width))

		window_height, row_width = window.getmaxyx()
		row_pos = window_height - 1
		corner_width = len(self.CORNER)
		result_width = row_width - corner_width - 1
		window.addstr(row_pos, 0, status[:result_width].ljust(result_width) + self.CORNER)
