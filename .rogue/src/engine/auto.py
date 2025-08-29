from clckwrkbdgr.math.auto import Autoexplorer
from . import math
from clckwrkbdgr.math import Size

class AutoMovement(object):
	""" Base class for any automovement mode.
	Supports both movement with target destination
	and endless auto-exploration modes.
	"""
	def next(self): # pragma: no cover
		""" Should return next movement shift
		or None, if automovement is finished.
		"""
		raise NotImplementedError()

class EndlessAreaExplorer(Autoexplorer, AutoMovement): # pragma: no cover -- TODO
	def __init__(self, dungeon):
		self.dungeon = dungeon
		super(EndlessAreaExplorer, self).__init__()
	def get_current_pos(self):
		return self.dungeon.scene.get_global_pos(self.dungeon.scene.get_player())
	def get_matrix(self):
		return self.dungeon.scene
	def is_passable(self, pos):
		return self.dungeon.scene.is_passable(pos)
	def is_valid_target(self, target):
		distance = target - self.get_current_pos()
		diff = abs(distance)
		if not (3 < diff.x < self.dungeon.scene.get_player().vision or 3 < diff.y < self.dungeon.scene.get_player().vision):
			return False
		return True
	def target_area_size(self):
		return Size(
				1 + 2 * self.dungeon.scene.get_player().vision,
				1 + 2 * self.dungeon.scene.get_player().vision,
				)

class BasicQueuedExplorer(AutoMovement):
	""" Base for any queued auto walker (targeted or free explorer).
	"""
	def __init__(self, game, dest=None):
		""" Is dest is None, starts free exploring mode.
		Otherwise walks to the dest and stops.
		"""
		self.game = game
		self.dest = dest
		self.queue = self.find_path()
	def find_target(self, wave): # pragma: no cover
		""" Should return point from the wave that is acceptable as a target.
		"""
		raise NotImplementedError()
	def find_path(self):
		""" Find free path from start and until find_target() returns suitable target.
		Otherwise return None.
		"""
		wave = math.Pathfinder(self.game.scene, vision=self.game.vision)
		self.wave = wave
		current_pos = self.game.scene.get_global_pos(self.game.scene.get_player())
		path = wave.run(current_pos, self.find_target)
		if not path:
			return None
		assert path[0] == current_pos
		return [next_p - prev_p for (prev_p, next_p) in zip(path[:-1], path[1:])]
	def next(self):
		""" If queue is ended and dest is specified, stops.
		Otherwise tries to restart by picking any new target.
		"""
		if not self.queue:
			if self.dest:
				return None
			self.queue = self.find_path()
			if not self.queue:
				return None
		return self.queue.pop(0)

class AutoWalk(BasicQueuedExplorer):
	""" Starts auto-walking towards dest, if possible.
	Does not start when monsters are around and produces event.
	"""
	def find_target(self, wave):
		return self.dest if self.dest in wave else None

class AutoExplorer(BasicQueuedExplorer):
	""" Starts auto-exploring in closed area, if there are unknown places.
	Picks any cell that has not explored neighbours as target.
	"""
	def find_target(self, wave):
		for target in sorted(wave):
			if self.wave.is_frontier(target):
				return target
		return None
