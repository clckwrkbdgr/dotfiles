from collections import namedtuple
from clckwrkbdgr.math import Point
import clckwrkbdgr.tui

Sprite = namedtuple('Sprite', 'sprite color')

class MainGame(clckwrkbdgr.tui.Mode):
	""" Main game mode: map, status line, messages.
	"""
	def __init__(self, game):
		self.game = game
		self.messages = []

	def get_map_shift(self): # pragma: no cover
		""" Shift of the topleft point of the map viewport
		from the topleft point of the screen.
		By default map display starts at the (0;0).
		Map viewport size will always be taken from get_viewrect().size
		"""
		return Point(0, 0)
	def get_viewrect(self): # pragma: no cover
		""" Should return Rect (in world coordinates)
		that defines what part of the current map is to be displayed
		in the main viewport.
		See Scene.iter_cells()
		"""
		raise NotImplementedError()
	def get_sprite(self, world_pos, cell_info): # pragma: no cover
		""" Should return Sprite object for given world pos
		and cell info (see Scene.get_cell_info()).
		"""
		raise NotImplementedError()
	
	def draw_map(self, ui):
		""" Redraws map according to get_viewrect() and get_sprite().
		"""
		view_rect = self.get_viewrect()
		for world_pos, cell_info in self.game.scene.iter_cells(view_rect):
			sprite = self.get_sprite(world_pos, cell_info)
			viewport_pos = world_pos - view_rect.topleft
			screen_pos = viewport_pos + self.get_map_shift()
			ui.print_char(screen_pos.x, screen_pos.y, sprite.sprite, sprite.color)
