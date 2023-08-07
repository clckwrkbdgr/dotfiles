import sys
import random
import curses
import logging
trace = logging.getLogger('rogue')
from .. import logging
from ..fs import SerializedEntity
from .. import xdg
from ..math import Point, Size, Rect, get_neighbours, sign
from .dungeon import Dungeon
from .auto import Autoexplorer

def main(stdscr):
	logging.init('rogue',
			debug='-d' in sys.argv,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	curses.curs_set(0)
	savefile = SerializedEntity(xdg.save_data_path('dotrogue')/'rogue.sav', 0, entity_name='dungeon', unlink=False, readable=True)
	savefile.load()
	if savefile.entity:
		dungeon = savefile.entity
	else:
		dungeon = Dungeon()
		savefile.reset(dungeon)
	game = Game(dungeon)
	game.run(stdscr)
	savefile.save()

class Game:
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
	VIEW_CENTER = Point(12, 12)

	def __init__(self, dungeon):
		self.dungeon = dungeon
		self.autoexplore = None
	def run(self, stdscr):
		while True:
			self.view(stdscr)
			if not self.control(stdscr):
				break
	def view(self, stdscr):
		for y in range(-self.VIEW_CENTER.y, 25 - self.VIEW_CENTER.y):
			for x in range(-self.VIEW_CENTER.x, 25 - self.VIEW_CENTER.x):
				stdscr.addstr(self.VIEW_CENTER.y + y, self.VIEW_CENTER.x + x, self.dungeon.get_sprite((x, y)))
		stdscr.addstr(0, 27, 'Time: {0}'.format(self.dungeon.time))
		stdscr.addstr(1, 27, 'X:{x} Y:{y}  '.format(x=self.dungeon.rogue.x, y=self.dungeon.rogue.y))
		stdscr.addstr(24, 27, '[autoexploring, press ESC...]' if self.autoexplore else '                             ')
		stdscr.refresh()
	def control(self, stdscr):
		char = stdscr.getch()
		control = self.CONTROLS.get(char)
		trace.debug('Curses char: {0}'.format(repr(char)))
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
				self.autoexplore = Autoexplorer()
				stdscr.nodelay(1)
				stdscr.timeout(100)
				return True
		elif control == 'ESC':
			trace.debug('Stopping self.autoexplore.')
			self.autoexplore = None
			stdscr.timeout(-1)
			stdscr.nodelay(0)
			return True
		try:
			self.dungeon.control(control)
		except SystemExit:
			trace.debug('Exiting...')
			return False
		return True

if __name__ == '__main__':
	curses.wrapper(main)
