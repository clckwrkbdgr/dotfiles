import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Rect, Size
import clckwrkbdgr.tui
from clckwrkbdgr.math.auto import Autoexplorer

class DungeonExplorer(Autoexplorer): # pragma: no cover
	def __init__(self, dungeon):
		self.dungeon = dungeon
		super(DungeonExplorer, self).__init__()
	def get_current_pos(self):
		return self.dungeon.get_player()
	def get_matrix(self):
		return self.dungeon.terrain
	def is_passable(self, cell):
		return cell == '.'
	def is_valid_target(self, target):
		distance = target - self.get_current_pos()
		diff = abs(distance)
		if not (3 < diff.x < 10 or 3 < diff.y < 10):
			return False
		return True
	def target_area_size(self):
		return Size(21, 21)

Keys = clckwrkbdgr.tui.Keymapping()
Keys.map('q', 'quit')
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
		self.autoexplorer_class = autoexplorer or DungeonExplorer
	def redraw(self, ui):
		view_rect = Rect(self.dungeon.get_player() - self.VIEW_CENTER, Size(25, 25))
		for pos, (terrain, _1, _2, monsters) in self.dungeon.iter_cells(view_rect):
			sprite = terrain
			if monsters:
				sprite = "@"
			ui.print_char(
					pos.x - view_rect.topleft.x,
					pos.y - view_rect.topleft.y,
					sprite,
					)
		ui.print_line(0, 27, 'Time: {0}'.format(self.dungeon.time))
		ui.print_line(1, 27, 'X:{x} Y:{y}  '.format(x=self.dungeon.get_player().x, y=self.dungeon.get_player().y))
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
				control = self.autoexplore.next()
				trace.debug('Autoexploring: {0}'.format(repr(control)))
				self.dungeon.shift_player(control)
			else:
				trace.debug('Starting self.autoexplore.')
				self.autoexplore = self.autoexplorer_class(self.dungeon)
		elif control == 'ESC':
			trace.debug('Stopping self.autoexplore.')
			self.autoexplore = None
			return True
		elif control == 'quit':
			return False
		elif isinstance(control, Point):
			self.dungeon.shift_player(control)
		return True
