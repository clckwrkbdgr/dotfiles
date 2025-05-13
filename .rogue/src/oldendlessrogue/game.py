import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr.math import Point
import clckwrkbdgr.tui
from .auto import Autoexplorer

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

class Game(clckwrkbdgr.tui.Mode):
	KEYMAPPING = Keys
	VIEW_CENTER = Point(12, 12)

	def __init__(self, dungeon, autoexplorer=None):
		self.dungeon = dungeon
		self.autoexplore = None
		self.autoexplorer_class = autoexplorer or Autoexplorer
	def redraw(self, ui):
		for y in range(-self.VIEW_CENTER.y, 25 - self.VIEW_CENTER.y):
			for x in range(-self.VIEW_CENTER.x, 25 - self.VIEW_CENTER.x):
				ui.print_char(
						self.VIEW_CENTER.x + x,
						self.VIEW_CENTER.y + y,
						self.dungeon.get_sprite((x, y)),
						)
		ui.print_line(0, 27, 'Time: {0}'.format(self.dungeon.time))
		ui.print_line(1, 27, 'X:{x} Y:{y}  '.format(x=self.dungeon.rogue.x, y=self.dungeon.rogue.y))
		ui.print_line(24, 27, '[autoexploring, press ESC...]' if self.autoexplore else '                             ')
	def nodelay(self):
		return self.autoexplore
	def action(self, control):
		trace.debug('Control: {0}'.format(repr(control)))
		trace.debug('Autoexplore={0}'.format(self.autoexplore))
		if control is None:
			return True
		if control == 'autoexplore':
			if self.autoexplore:
				control = self.autoexplore.process(self.dungeon)
				trace.debug('Autoexploring: {0}'.format(repr(control)))
			else:
				trace.debug('Starting self.autoexplore.')
				self.autoexplore = self.autoexplorer_class()
				return True
		elif control == 'ESC':
			trace.debug('Stopping self.autoexplore.')
			self.autoexplore = None
			return True
		try:
			self.dungeon.control(control)
		except SystemExit:
			trace.debug('Exiting...')
			return False
		return True
