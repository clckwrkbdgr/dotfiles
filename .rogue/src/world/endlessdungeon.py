from clckwrkbdgr.math import Point, Size, Rect
from clckwrkbdgr.math.grid import EndlessMatrix
from .. import engine
from ..engine import scene, terrain, actors, appliances
from ..engine import auto

class Scene(scene.Scene):
	BLOCK_SIZE = Size(32, 32)
	BUILDERS = None
	def __init__(self):
		self.terrain = None
		self.monsters = []
		self.appliances = []
		self.builder = type(self).BUILDERS()
	def generate(self, id):
		self.terrain = EndlessMatrix(block_size=self.BLOCK_SIZE, builder=self.builder.build_block)
		self._player_pos = self.builder._start_pos
		self.appliances[:] = self.builder.appliances
	def save(self, stream): # pragma: no cover -- TODO
		self.terrain.save(stream)
		stream.write(len(self.monsters))
		for monster in self.monsters:
			monster.save(stream)
		stream.write(len(self.appliances))
		for appliance in self.appliances:
			appliance.save(stream)
	def load(self, stream): # pragma: no cover -- TODO
		super(Scene, self).load(stream)
		self.terrain = EndlessMatrix(block_size=self.BLOCK_SIZE, builder=self.builder.build_block, cell_type=terrain.Terrain)
		self.terrain.load(stream)
		monsters = stream.read(int)
		for _ in range(monsters):
			self.monsters.append(actors.Actor.load(stream))
		_appliances = stream.read(int)
		for _ in range(_appliances):
			self.appliances.append(appliances.ObjectAtPos.load(stream))
	def enter_actor(self, actor, location):
		actor.pos = self._player_pos
		self.monsters.append(actor)
	def exit_actor(self, actor):
		self.monsters.remove(actor)
	@classmethod
	def get_autoexplorer_class(cls): # pragma: no cover -- TODO
		return auto.EndlessAreaExplorer
	def get_area_rect(self): # pragma: no cover -- TODO
		return Rect(
				self.terrain.shift - Point(Size(self.terrain.block_size)),
				self.terrain.block_size * 3,
				)
	def valid(self, pos): # pragma: no cover -- TODO
		return self.terrain.valid(pos)
	def recalibrate(self, vantage_point, marging=None):
		self.terrain.recalibrate(vantage_point)
	def get_cell_info(self, pos):
		cell = self.terrain.cell(pos)
		return cell, [], list(self.iter_appliances_at(pos)), list(self.iter_actors_at(pos))
	def iter_appliances_at(self, pos):
		for appliance in self.appliances:
			if appliance.pos == pos:
				yield appliance.obj
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
