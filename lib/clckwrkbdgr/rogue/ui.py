import curses
import logging
trace = logging.getLogger('rogue')
from ..math import Point

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
		self.nodelay = False
	def run(self):
		curses.wrapper(self._run)
	def _run(self, stdscr):
		curses.curs_set(0)
		self.stdscr = stdscr
		return self.game.run(self)

	def draw_tile(self, x, y, sprite):
		self.stdscr.addstr(y, x, sprite)
	def print_line(self, index, line):
		self.stdscr.addstr(index, 27, line)
	def sync(self):
		self.stdscr.refresh()

	def get_control(self, nodelay=False):
		if self.nodelay != bool(nodelay):
			if nodelay:
				self.stdscr.nodelay(1)
				self.stdscr.timeout(100)
			else:
				self.stdscr.timeout(-1)
				self.stdscr.nodelay(0)
			self.nodelay = bool(nodelay)

		char = self.stdscr.getch()
		trace.debug('Curses char: {0}'.format(repr(char)))
		control = self.CONTROLS.get(char)
		return control
