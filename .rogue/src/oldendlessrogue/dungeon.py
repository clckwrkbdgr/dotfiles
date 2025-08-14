from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.math.grid import EndlessMatrix
from . import builders
from .. import engine
from ..engine import actors, scene
from ..engine import ui, auto

class Dungeon(engine.Game):
	PLAYER_TYPE = None
	def __init__(self):
		super(Dungeon, self).__init__()
	def get_scene_class(self): return Scene
	def generate(self, start_scene_id):
		self.scene = self.get_scene_class()()
		self.scene.generate(start_scene_id)
		self.scene.enter_actor(self.make_player(), None)
	def make_player(self):
		return self.PLAYER_TYPE(None)
	def load(self, state):
		self.scene = self.get_scene_class()()
		old_builder = self.scene.builder
		self.__dict__.update(state)
		if 'playing_time' not in state:
			self.playing_time = state.get('time', 0)
		self.scene.builder = old_builder
		self.scene.terrain.builder = self.scene.builder.build_block
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
		self.scene.terrain.recalibrate(self.scene.get_player().pos)

class Scene(scene.Scene):
	BLOCK_SIZE = Size(32, 32)
	BUILDERS = None
	def __init__(self):
		self.terrain = None
		self.monsters = []
		self.builder = self.BUILDERS()
	def generate(self, id):
		self.terrain = EndlessMatrix(block_size=self.BLOCK_SIZE, builder=self.builder.build_block, default_value=builders.EndlessVoid())
		self._player_pos = Point(self.builder.place_rogue(self.terrain))
	def enter_actor(self, actor, location):
		actor.pos = self._player_pos
		self.monsters.append(actor)
	@classmethod
	def get_autoexplorer_class(cls): # pragma: no cover -- TODO
		return auto.EndlessAreaExplorer
	def valid(self, pos): # pragma: no cover -- TODO
		return self.terrain.valid(pos)
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
	def iter_active_monsters(self):
		return self.monsters
