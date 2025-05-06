import curses
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr.math import Point
import clckwrkbdgr.tui

Keys = clckwrkbdgr.tui.Keymapping()
Keys.map('q', SystemExit)
Keys.map('o', 'autoexplore')
Keys.map('h', Point(-1,  0))
Keys.map('j', Point( 0, +1))
Keys.map('k', Point( 0, -1))
Keys.map('l', Point(+1,  0))
Keys.map('y', Point(-1, -1))
Keys.map('u', Point(+1, -1))
Keys.map('b', Point(-1, +1))
Keys.map('n', Point(+1, +1))
Keys.map(clckwrkbdgr.tui.Key.ESCAPE, 'ESC')

class Curses: # pragma: no cover -- TODO unit tests for curses or manual testing utility.
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
		return self.ui.get_control(Keys, nodelay=nodelay)
