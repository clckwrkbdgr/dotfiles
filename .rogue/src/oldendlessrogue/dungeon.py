from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.math.grid import EndlessMatrix
from . import builders
from .. import engine
from ..engine import actors, scene

class Player(actors.Monster):
	_sprite = "@"

class Dungeon(engine.Game):
	def __init__(self, builder=None):
		super(Dungeon, self).__init__()
		self.builder = builder or builders.Builders()
		self.scene = Scene()
		self.time = 0
	def is_finished(self): # pragma: no cover -- TODO
		return False
	def generate(self):
		self.scene.terrain = EndlessMatrix(block_size=self.scene.BLOCK_SIZE, builder=self.builder.build_block, default_value=builders.EndlessVoid())
		self.scene.monsters.append(Player(self.builder.place_rogue(self.scene.terrain)))
	def load(self, state):
		self.__dict__.update(state)
		if 'time' not in state:
			self.time = 0
		self.scene.terrain.builder = self.builder.build_block
	def save(self, state): # pragma: no cover -- TODO
		data = {}
		data.update(self.__dict__)
		del data['rng']
		state.update(data)
	def shift_monster(self, monster, shift):
		new_pos = monster.pos + shift
		if self.scene.is_passable(new_pos):
			monster.pos = new_pos
	def finish_action(self):
		self.scene.terrain.recalibrate(self.scene.get_player().pos)
		self.time += 1

class Scene(scene.Scene):
	BLOCK_SIZE = Size(32, 32)
	def __init__(self):
		self.terrain = None
		self.monsters = []
	def get_cell_info(self, pos):
		cell = self.terrain.cell(pos) or builders.EndlessVoid()
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
	def is_passable(self, pos):
		return self.terrain.cell(pos) and self.terrain.cell(pos).passable
