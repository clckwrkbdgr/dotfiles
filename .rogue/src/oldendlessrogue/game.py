import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Rect, Size
import clckwrkbdgr.tui
from ..engine import ui

Keys = clckwrkbdgr.tui.Keymapping()
MOVEMENT = {
		'h' : Point(-1, 0),
		'j' : Point(0, 1),
		'k' : Point(0, -1),
		'l' : Point(1, 0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),
		}

class Game(ui.MainGame):
	KEYMAPPING = Keys
	VIEW_CENTER = Point(12, 12)
	INDICATORS = [
			ui.Indicator(Point(27, 0), 29, lambda self:'Time: {0}'.format(self.game.time)),
			ui.Indicator(Point(27, 1), 29, lambda self:'X:{x} Y:{y}  '.format(x=self.game.scene.get_player().pos.x, y=self.game.scene.get_player().pos.y)),
			ui.Indicator(Point(27, 24), 29, lambda self:'[autoexploring, press ESC...]' if self.dungeon.autoexplore else ''),
			]

	def __init__(self, dungeon):
		super(Game, self).__init__(dungeon)
		self.dungeon = self.game
	def get_viewrect(self):
		return Rect(self.dungeon.scene.get_player().pos - self.VIEW_CENTER, Size(25, 25))
	def get_message_line_rect(self):
		return Rect(Point(0, 25), Size(80, 1))
	@Keys.bind('q')
	def quit(self):
		return True
	@Keys.bind('o')
	def start_autoexplore(self):
		if True:
			if True:
				trace.debug('Starting self.autoexplore.')
				self.dungeon.start_autoexplore()
	@Keys.bind(list('hjklyubn'), lambda key:MOVEMENT[str(key)])
	def move_player(self, control):
		if True:
			self.dungeon.shift_monster(self.dungeon.scene.get_player(), control)
			self.dungeon.finish_action()
