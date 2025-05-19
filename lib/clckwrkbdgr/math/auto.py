import logging
trace = logging.getLogger(__name__)
from clckwrkbdgr.math import algorithm
from clckwrkbdgr.math import Point, Rect, sign, Direction

class Autoexplorer:
	""" Simple randomized auto-exploring algorithm over Matrix-like objects.
	Places target points roughly in the same (initially randomly picked) direction,
	which may change slowly over time, emulating natural wandering.
	Uses standard Wave algorithm to calculate its path.
	"""
	class Wave(algorithm.MatrixWave):
		def __init__(self, engine, *args, **kwargs):
			self.engine = engine
			super(Autoexplorer.Wave, self).__init__(*args, **kwargs)
		def is_passable(self, p, _):
			return self.engine.is_passable(self.matrix.cell(p))

	def __init__(self):
		self.path = None
		self.previous_direction = None

	def randrange(self, start, stop):
		""" Returns random integer value between start and stop.
		Default implementation uses standard random module (random.randrange).
		Can be overridden to use custom pseudo-random mechanism.
		"""
		import random
		return random.randrange(start, stop)
	def get_current_pos(self): # pragma: no cover
		""" Should return current position of the actor. """
		raise NotImplementedError()
	def get_matrix(self): # pragma: no cover
		""" Should return Matrix-like object.
		It should implement at least methods .cell() and .valid()
		"""
		raise NotImplementedError()
	def is_passable(self, cell): # pragma: no cover
		""" Should return True if given cell object is passable. """
		raise NotImplementedError()
	def target_area_size(self): # pragma: no cover
		""" Should return Rect object from which target point is picked,
		usually around current position.
		"""
		raise NotImplementedError()
	def is_valid_target(self, target): # pragma: no cover
		""" Should employ additional checks for target points.
		E.g. if target area has non-rectangular shape,
		or it should have some distance from the current position etc.
		"""
		raise NotImplementedError()

	def next(self):
		""" Returns next step (shift in movement).
		Auto-picks new target point when needed and plans a path to it.
		Doesn't ever stop; to stop autoexploring, recreate object from scratch.
		It's not safe to manually change actor's position during autoexploring,
		as currently planned path is stored as a sequence of relative shifts,
		so it's better to stop autoexploring completely.
		"""
		if not self.path:
			self._plan_path()
		direction = self.path.pop(0)
		self.previous_direction += direction
		return direction
	def _plan_path(self):
		target = self.get_current_pos()
		target_area = Rect(
			topleft=self.get_current_pos() - self.target_area_size() / 2,
			size=self.target_area_size(),
			)
		for _ in range(target_area.width * target_area.height):
			target = Point(
					self.randrange(target_area.left, target_area.right),
					self.randrange(target_area.top, target_area.bottom),
					)
			trace.debug('Autoexplorer target: trying {0}'.format(target))
			if not self.is_passable(self.get_matrix().cell(target)):
				trace.debug('Autoexplorer target: {0}: not passable'.format(target))
				continue
			if not self.is_valid_target(target):
				trace.debug('Autoexplorer target: not suitable target: {0}'.format(target))
				continue
			direction = Direction.from_points(self.get_current_pos(), target)
			trace.debug('Autoexplorer target: selected direction: {0}'.format(direction))
			if self.previous_direction:
				self.previous_direction = Point(
						sign(self.previous_direction.x),
						sign(self.previous_direction.y),
						)
				trace.debug('Autoexplorer target: previous direction: {0}'.format(self.previous_direction))
				if self.previous_direction.x == 0:
					old_directions = [
							Point(-1, 0),
							Point(-1, -self.previous_direction.y),
							Point(0, -self.previous_direction.y),
							Point(1, -self.previous_direction.y),
							Point(1, 0),
							]
				elif self.previous_direction.y == 0:
					old_directions = [
							Point(0, -1),
							Point(-self.previous_direction.x, -1),
							Point(-self.previous_direction.x, 0),
							Point(-self.previous_direction.x, 1),
							Point(0, 1),
							]
				else:
					old_directions = [
							Point(self.previous_direction.x, -self.previous_direction.y),
							Point(0, -self.previous_direction.y),
							Point(-self.previous_direction.x, -self.previous_direction.y),
							Point(-self.previous_direction.x, 0),
							Point(-self.previous_direction.x, self.previous_direction.y),
							]
				trace.debug('Autoexplorer target: old direction fan: {0}'.format(old_directions))
				if direction in old_directions:
					trace.debug('Autoexplorer target: selected direction is old.')
					continue
			self.previous_direction = Point(0, 0)
			trace.debug('Autoexplorer target: good, picking {0}'.format(target))
			break
		wave = self.Wave(self, self.get_matrix(), target_area)
		trace.debug('Autoexplorer forming path: {0} -> {1}'.format(self.get_current_pos(), target))
		path = wave.run(self.get_current_pos(), target)
		trace.debug('Autoexplorer wave: {0}'.format(path))
		self.path = list(b - a for a, b in zip(path, path[1:]))
		trace.debug('Autoexplorer sequence: {0}'.format(self.path))
