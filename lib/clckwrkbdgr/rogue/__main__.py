import sys
import random
import logging
trace = logging.getLogger('rogue')
from .. import logging
from ..fs import SerializedEntity
from .. import xdg
from ..math import Point, Size, Rect, get_neighbours, sign
from .dungeon import Dungeon
from .auto import Autoexplorer
from .ui import Curses

def main():
	logging.init('rogue',
			debug='-d' in sys.argv,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	savefile = SerializedEntity(xdg.save_data_path('dotrogue')/'rogue.sav', 0, entity_name='dungeon', unlink=False, readable=True)
	savefile.load()
	if savefile.entity:
		dungeon = savefile.entity
	else:
		dungeon = Dungeon()
		savefile.reset(dungeon)
	game = Game(dungeon)
	gui = Curses(game)
	gui.run()
	savefile.save()

class Game:
	VIEW_CENTER = Point(12, 12)

	def __init__(self, dungeon):
		self.dungeon = dungeon
		self.autoexplore = None
	def run(self, ui):
		while True:
			self.view(ui)
			if not self.control(ui):
				break
	def view(self, ui):
		for y in range(-self.VIEW_CENTER.y, 25 - self.VIEW_CENTER.y):
			for x in range(-self.VIEW_CENTER.x, 25 - self.VIEW_CENTER.x):
				ui.draw_tile(
						self.VIEW_CENTER.x + x,
						self.VIEW_CENTER.y + y,
						self.dungeon.get_sprite((x, y)),
						)
		ui.print_line(0, 'Time: {0}'.format(self.dungeon.time))
		ui.print_line(1, 'X:{x} Y:{y}  '.format(x=self.dungeon.rogue.x, y=self.dungeon.rogue.y))
		ui.print_line(24, '[autoexploring, press ESC...]' if self.autoexplore else '                             ')
		ui.sync()
	def control(self, ui):
		control = ui.get_control(nodelay=self.autoexplore)
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

if __name__ == '__main__':
	main()
