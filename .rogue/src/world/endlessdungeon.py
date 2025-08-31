from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.math.grid import EndlessMatrix
from .. import engine
from ..engine import scene
from ..engine import auto

class Scene(scene.Scene):
	BLOCK_SIZE = Size(32, 32)
	BUILDERS = None
	def __init__(self):
		self.terrain = None
		self.monsters = []
		self.builder = self.BUILDERS()
	def generate(self, id):
		self.terrain = EndlessMatrix(block_size=self.BLOCK_SIZE, builder=self.builder.build_block, default_value=self.builder.void)
		self._player_pos = self.builder._start_pos
	def enter_actor(self, actor, location):
		actor.pos = self._player_pos
		self.monsters.append(actor)
	@classmethod
	def get_autoexplorer_class(cls): # pragma: no cover -- TODO
		return auto.EndlessAreaExplorer
	def valid(self, pos): # pragma: no cover -- TODO
		return self.terrain.valid(pos)
	def recalibrate(self, vantage_point, marging=None):
		self.terrain.recalibrate(vantage_point)
	def get_cell_info(self, pos):
		cell = self.terrain.cell(pos) or self.builder.void
		return cell, [], [], list(self.iter_actors_at(pos))
	def iter_actors_at(self, pos, with_player=False):
		for monster in self.monsters:
			if monster.pos == pos:
				yield monster
	def iter_cells(self, view_rect):
		for y in range(view_rect.topleft.y, view_rect.bottomright.y + 1):
			for x in range(view_rect.topleft.x, view_rect.bottomright.x + 1):
				pos = Point(x, y)
				yield pos, self.get_cell_info(pos)
	def get_player(self):
		return next(iter(self.monsters))
	def iter_active_monsters(self):
		return self.monsters
