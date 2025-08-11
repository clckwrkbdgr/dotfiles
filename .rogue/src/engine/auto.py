from clckwrkbdgr.math.auto import Autoexplorer

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
		super(DungeonExplorer, self).__init__()
	def get_current_pos(self):
		return self.dungeon.scene.get_player().pos
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
