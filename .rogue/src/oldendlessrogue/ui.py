import curses
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr.math import Point
import clckwrkbdgr.tui

class Curses: # pragma: no cover -- TODO unit tests for curses or manual testing utility.
	CONTROLS = {(ord(k) if isinstance(k, str) else k):v for k,v in {
		'q' : SystemExit,
		'o' : 'autoexplore',
		'h' : Point(-1,  0),
		'j' : Point( 0, +1),
		'k' : Point( 0, -1),
		'l' : Point(+1,  0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),

		-1 : 'autoexplore',
		27 : 'ESC',
		}.items()}

	def __init__(self, game):
		self.game = game
		self.stdscr = None
	def run(self):
		with clckwrkbdgr.tui.Curses() as ui:
			self.ui = ui
			self.stdscr = ui.window
			return self.game.run(self)

	def draw_tile(self, x, y, sprite):
		self.ui.window.addstr(y, x, sprite)
	def print_line(self, index, line):
		self.ui.window.addstr(index, 27, line)
	def sync(self):
		self.ui.window.refresh()

	def get_control(self, nodelay=False):
		char = self.ui.get_control(nodelay=nodelay)
		trace.debug('Curses char: {0}'.format(repr(char)))
		control = self.CONTROLS.get(char.value)
		return control
