from . import app

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
