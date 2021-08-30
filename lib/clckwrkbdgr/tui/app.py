import types
try:
	ClassType = (type, types.ClassType)
except: # pragma: no cover
	ClassType = type
from ._base import Key, ExceptionScreen

class MVC(object): # pragma: no cover -- TODO curses
	""" Model-View-Controller for curses TUI.
	Should be subclassed to implement custom functionality.
	Model: user-specified data object.
	View: displays user-specified output in curses window.
	Controller: accepts pressed key from curses and performs user-defined actions.
	"""
	def __init__(self, data=None):
		self.data = data
		self._first_view = True
	def view(self, window):
		""" Displays output on window and refreshes.
		See also user-customized method _view()
		"""
		if self._first_view:
			if self.full_redraw():
				window.erase()
			self._first_view = False
		result = self._view(window)
		window.refresh()
		return result
	def control(self, key):
		""" Processes pressed key.
		Returns new MVC instance.
		See also user-customized method _control()
		"""
		new_instance = self._control(Key(key))
		if not new_instance:
			return self
		if isinstance(new_instance, ClassType):
			new_instance = new_instance(self.data)
		return new_instance

	def full_redraw(self):
		""" Should return True if full redraw is expected upon entering this MVC.
		It will be performed only once at first enter.
		If class field _full_redraw is defined, it will be used by default.
		"""
		if hasattr(self, '_full_redraw'):
			return self._full_redraw
		return False
	def _view(self, window):
		""" Override this to display data on curses window. """
		raise NotImplementedError
	def _control(self, key):
		""" Override this to process pressed key (of type tui.Key)
		and perform correspoding actions.
		Should return either manually created MVC subclass instance
		or subclass type. In case of latter current data should be passed to the new MVC.
		When return value is None, current MVC instance should be re-used again.
		"""
		raise NotImplementedError

class AppExit(Exception): # pragma: no cover
	def __init__(self, return_code=None):
		self.return_code = return_code

class App(object): # pragma: no cover -- TODO curses
	def __init__(self, window):
		self.window = window
	def preprocess(self, mode):
		""" Executes right before MVC at each iteration.
		Override this to perform any pre-processing.
		"""
		return NotImplemented
	def run(self, start_mode):
		""" Starts loop of MVC modes.
		Breaks loop when AppExit is caught and returns it return_code.
		Every other exception is handled by tui.ExceptionScreen.
		"""
		current_mode = start_mode
		while True:
			with ExceptionScreen(self.window):
				self.preprocess(current_mode)
				current_mode.view(self.window)
				try:
					current_mode = current_mode.control(self.window.getch())
				except AppExit as e:
					return e.return_code
		return None