import clckwrkbdgr.math
import clckwrkbdgr.math.algorithm

def is_diagonal(shift):
	""" Returns True if shift is exactly 1x1 cell diagonal movement. """
	return abs(shift.x) + abs(shift.y) == 2

class Vision(object):
	""" Basic vision/memory capabilities.
	Should support fields or vision and remembered/visited places.
	"""
	def is_explored(self, pos): # pragma: no cover
		""" Should return True if given position is visible or
		was visited and/or seen.
		"""
		raise NotImplementedError()

class Pathfinder(clckwrkbdgr.math.algorithm.MatrixWave):
	""" Pathfinder algorithm on Scene
	which considers passable and/or explored cells.
	. """
	def __init__(self, *args, **kwargs):
		""" Creates pathfinder on given Scene.
		Accepts Vision object as kwarg "vision"
		"""
		if kwargs.get('vision'):
			self.vision = kwargs.get('vision')
			del kwargs['vision']
		super(Pathfinder, self).__init__(*args, **kwargs)
	def is_frontier(self, target):
		for p in clckwrkbdgr.math.get_neighbours(self.matrix, target, with_diagonal=True):
			if not self.vision.is_explored(p):
				return True
		return False
	def is_passable(self, p, from_point):
		""" Movement is allowed if cell is passable, explored (seen and/or visible)
		and diagonal movement is allowed between two cells.
		"""
		if not self.vision.is_explored(p):
			return False
		if not self.matrix.is_passable(p):
			return False
		return self.matrix.allow_movement_direction(from_point, p)
