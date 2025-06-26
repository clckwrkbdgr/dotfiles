from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.math.grid import EndlessMatrix
from . import builders
from .. import engine

class Dungeon(engine.Game):
	BLOCK_SIZE = Size(32, 32)

	def __init__(self, builder=None):
		super(Dungeon, self).__init__()
		self.builder = builder or builders.Builders()
		self.terrain = None
		self.monsters = []
		self.time = 0
	def is_finished(self): # pragma: no cover -- TODO
		return False
	def generate(self):
		self.terrain = EndlessMatrix(block_size=self.BLOCK_SIZE, builder=self.builder.build_block)
		self.monsters.append(Point(self.builder.place_rogue(self.terrain)))
	def load(self, state):
		self.__dict__.update(state)
		if 'time' not in state:
			self.time = 0
		self.terrain.builder = self.builder.build_block
	def save(self, state): # pragma: no cover -- TODO
		data = {}
		data.update(self.__dict__)
		del data['rng']
		state.update(data)
	def get_cell_info(self, pos):
		return self.terrain.cell(pos), [], [], list(self.iter_actors_at(pos))
	def iter_actors_at(self, pos, with_player=False):
		for _ in self.monsters:
			if _ == pos:
				yield _
	def iter_cells(self, view_rect):
		for y in range(view_rect.topleft.y, view_rect.bottomright.y + 1):
			for x in range(view_rect.topleft.x, view_rect.bottomright.x + 1):
				pos = Point(x, y)
				yield pos, self.get_cell_info(pos)
	def get_player(self):
		return next(iter(self.monsters))
	def get_sprite(self, pos):
		terrain, objects, items, monsters = self.get_cell_info(pos)
		if monsters:
			return "@"
		return terrain
	def is_passable(self, pos):
		return self.terrain.cell(pos) == '.'
	def shift_player(self, shift):
		new_pos = self.get_player() + shift
		if self.is_passable(new_pos):
			self.monsters[0] = new_pos
			self.terrain.recalibrate(self.get_player())
		self.time += 1
