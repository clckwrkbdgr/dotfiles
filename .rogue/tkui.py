import sys
import contextlib
import time, threading
import tkinter
from clckwrkbdgr.math import Point
from clckwrkbdgr.math.grid import Matrix
from clckwrkbdgr.tui import Key, Mode

class Cursor(object): # pragma: no cover -- TODO
	def __init__(self, engine):
		self._pos = Point(0, 0)
		self.engine = engine
	def move(self, x, y):
		self._pos = Point(x, y)

class TkUI(object):
	def __init__(self): # pragma: no cover -- TODO
		self.root = None
		self.view = None
		self._destroying = False
		self._nodelay = False
		self.window = Matrix((100, 30), ' ')
		self.keypresses = []
		self._cursor = None
		self._font_size = 8
	def __enter__(self): # pragma: no cover -- TODO
		self.root = tkinter.Tk()

		outer_frame = tkinter.Frame(self.root)
		outer_frame.pack(fill='both', expand=True)
		canvas = tkinter.Canvas(outer_frame)
		canvas.pack(side="left", fill="both", expand=True)
		v_scrollbar = tkinter.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
		v_scrollbar.pack(side="right", fill="y")
		h_scrollbar = tkinter.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
		h_scrollbar.pack(side="bottom", fill="x")
		canvas.configure(yscrollcommand=v_scrollbar.set)
		canvas.configure(xscrollcommand=h_scrollbar.set)
		canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion = canvas.bbox("all")))
		inner_frame = tkinter.Frame(canvas)
		canvas.create_window((0, 0), window=inner_frame, anchor="nw")

		menu_frame = tkinter.Frame(inner_frame)
		menu_frame.pack()
		tkinter.Button(menu_frame, text='Exit', command=self.force_exit).pack(side='left')
		tkinter.Button(menu_frame, text='Font+', command=self.font_bigger).pack(side='left')
		tkinter.Button(menu_frame, text='Font-', command=self.font_smaller).pack(side='left')

		self.view = tkinter.Label(
				inner_frame,
				text=self.window.tostring(),
				font=("Courier", self._font_size),
				)
		self.view.pack()

		keys = [
				chr(27) + 'S~gdieOayku',
				'?vxwUWTEfh.l',
				'QcqCMo><mbjn',
				'prstz ',
				]
		for keyline in keys:
			frame = tkinter.Frame(inner_frame)
			frame.pack()
			for key in keyline:
				tkinter.Button(frame, text=key, command=lambda _key=key:self.add_keypress(_key)).pack(side='left')
		return self
	def __exit__(self, *_targs): # pragma: no cover -- TODO
		pass
	def force_exit(self):
		self._destroying = True
		self._loop.modes.clear()
		self.root.destroy()
	def add_keypress(self, key):
		self.keypresses.append(key)
	def font_smaller(self):
		self._font_size = max(1, self._font_size - 1)
		self.view.config(font=("Courier", self._font_size))
	def font_bigger(self):
		self._font_size = min(72, self._font_size + 1)
		self.view.config(font=("Courier", self._font_size))

	@contextlib.contextmanager
	def redraw(self, clean=False): # pragma: no cover -- TODO
		try:
			if clean:
				self.window.clear(' ')
			yield self
		finally:
			if self._cursor:
				self.window.set_cell(self._cursor._pos, 'X')
			self.view.config(text=self.window.tostring())
	def print_char(self, x, y, sprite, color=None): # pragma: no cover -- TODO
		self.window.set_cell((x, y), sprite[0])
	def print_line(self, row, col, line, color=None): # pragma: no cover -- TODO
		for i in range(len(line)):
			self.window.set_cell((col + i, row), line[i])

	def cursor(self, on=True): # pragma: no cover -- TODO
		""" Switches cursor on/off and returns Cursor object, if on.
		"""
		if on:
			if self._cursor is None:
				self._cursor = Cursor(self)
			return self._cursor
		if self._cursor is not None:
			self._cursor = None
		return None
	
	def get_keypress(self, nodelay=False, timeout=100): # pragma: no cover -- TODO
		""" Returns Key object for the pressed key.
		Waits for keypress, unless nodelay is specified - in that case
		returns key immediately (after specified timeout msec)
		or None, if no keys are pressed.
		"""
		nodelay = bool(nodelay)
		if self._nodelay != nodelay:
			self._nodelay = nodelay

		# Emulating (possibly nodelay) getch.
		while not self.keypresses:
			if self._destroying:
				return 0
			time.sleep(timeout/1000.)
			if self._nodelay:
				break
		if self.keypresses:
			ch = ord(self.keypresses.pop(0))
		else:
			ch = -1

		if ch == -1:
			return None
		return Key(ch)
	def get_control(self, keymapping, nodelay=False, timeout=100, bind_self=None, callback_args=None, callback_kwargs=None): # pragma: no cover -- TODO
		""" Returns mapped object from keymapping for the pressed key
		or None in case of unknown key.
		In nodelay mode tries to return keymapping for None,
		or None value itself if no such keymapping found.
		See get_keypress and Keymapping.get for other details.
		Callback will be detected and executed automatically.
		If callback_args and/or callback_kwargs are given and callback is bound,
		they will be passed as args/kwargs to the callback.
		"""
		key = self.get_keypress(nodelay=nodelay, timeout=timeout)
		control = keymapping.get(key, bind_self=bind_self)
		if callable(control):
			callback_args = callback_args or []
			callback_kwargs = callback_kwargs or {}
			control = control(*callback_args, **callback_kwargs)
		return control

class ModeLoop(object): # pragma: no cover -- TODO
	""" Main mode loop.
	Runs redraw/input until aborted by Mode.action().
	If .TRANSPARENT is not True, cleans screen before redrawing.
	"""
	def __init__(self, ui):
		self.ui = ui
		self.ui._loop = self
		self.modes = []
	def run(self, mode):
		""" Start loop from the given ("main") mode.
		Runs until the last mode is exited.
		"""
		self.modes.append(mode)
		thread = threading.Thread(target=self._thread_func)
		thread.start()
		self.ui.root.mainloop()
		thread.join()
	def _thread_func(self):
		while self.run_iteration() or self.modes:
			pass
		self.ui.root.after(10, self.ui.root.destroy)
	def run_iteration(self):
		""" Single iteration: redraw + user action. """
		result = True
		self.redraw()
		result = self.action()
		return result
	def redraw(self):
		""" Redraws all modes, starting from the first non-transparent mode from the end of the current stack. """
		visible = []
		for mode in reversed(self.modes):
			visible.append(mode)
			if not mode.TRANSPARENT:
				break
		for mode in reversed(visible):
			with self.ui.redraw(clean=not mode.TRANSPARENT):
				mode.redraw(self.ui)
	def mode_action(self, mode):
		""" Perform user action for a specific mode.
		Any callbacks are bound to the mode (see also Mode.get_bind_callback_args).
		Returns False if mode is done and should be closed, otherwise True.
		"""
		keymapping = mode.get_keymapping()
		if keymapping:
			control = self.ui.get_control(keymapping, nodelay=mode.nodelay(), bind_self=mode, callback_args=mode.get_bind_callback_args())
		else:
			control = self.ui.get_keypress(nodelay=mode.nodelay())

		new_mode = None
		if isinstance(control, Mode):
			new_mode = control
			control = None

		result = mode.action(control)

		if not result:
			self.modes.pop()
		if new_mode:
			self.modes.append(new_mode)

		return result
	def action(self):
		""" Perform user actions for the current stack of modes. """
		current_mode = self.modes[-1]
		if not current_mode.pre_action():
			self.modes.pop()
			return False
		return self.mode_action(current_mode)

