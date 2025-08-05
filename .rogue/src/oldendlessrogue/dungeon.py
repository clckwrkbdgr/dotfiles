from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.math.grid import EndlessMatrix
from . import builders
from .. import engine
from clckwrkbdgr.math.auto import Autoexplorer
from ..engine import actors, scene
from ..engine import ui

class DungeonExplorer(Autoexplorer): # pragma: no cover
	def __init__(self, dungeon):
		self.dungeon = dungeon
		super(DungeonExplorer, self).__init__()
	def get_current_pos(self):
		return self.dungeon.scene.get_player().pos
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

class Dungeon(engine.Game):
	PLAYER_TYPE = None
	def __init__(self, builder=None):
		super(Dungeon, self).__init__()
		self.builder = builder or builders.Builders()
		self.scene = Scene()
		self.time = 0
		self.autoexplore = None
	def in_automovement(self):
		return self.autoexplore
	def automove(self, dest=None): # pragma: no cover
		self.autoexplore = DungeonExplorer(self)
	def perform_automovement(self):
		if not self.autoexplore:
			return
		control = self.autoexplore.next()
		self.move_actor(self.scene.get_player(), control)
	def stop_automovement(self):
		self.autoexplore = None
	def is_finished(self): # pragma: no cover -- TODO
		return False
	def generate(self):
		self.scene.terrain = EndlessMatrix(block_size=self.scene.BLOCK_SIZE, builder=self.builder.build_block, default_value=builders.EndlessVoid())
		self.scene.monsters.append(self.PLAYER_TYPE(self.builder.place_rogue(self.scene.terrain)))
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
	def move_actor(self, monster, shift):
		new_pos = monster.pos + shift
		if self.scene.is_passable(new_pos):
			monster.pos = new_pos
		monster.spend_action_points()
	def process_others(self):
		if not self.scene.get_player().has_acted():
			return
		self.scene.terrain.recalibrate(self.scene.get_player().pos)
		self.time += 1
		self.scene.get_player().add_action_points()

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
