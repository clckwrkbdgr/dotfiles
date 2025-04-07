from collections import namedtuple
import copy
import itertools
import logging
Log = logging.getLogger('rogue')

import clckwrkbdgr.math
from clckwrkbdgr.math import Point, Size, Rect, distance, Matrix
from clckwrkbdgr.math import algorithm

"""
class MyWave(algorithm.MatrixWave):
	def __init__(self, matrix, is_passable):
		super().__init__(matrix)
		self._is_passable = is_passable
	def is_passable(self, *args):
		return self._is_passable(*args)

def find_path(matrix, start, is_passable, find_target):
	wave = MyWave(matrix, is_passable)
	return wave.run(start, find_target)
	"""

def in_line_of_sight(start, target, is_transparent):
	""" Returns True if target is in direct line of sight (bresenham)
	and every cell on the way is_transparent (callable, should return bool for Point).
	"""
	for pos in algorithm.bresenham(start, target):
		if not is_transparent(pos) and pos != target:
			return False
	return True

class FieldOfView:
	""" Updatable field of view for grid maps.
	"""
	def __init__(self, radius):
		""" Creates field of view with size of 2R + 1.
		Does not perform initial update.
		"""
		self.sight = Matrix(Size(1 + radius * 2, 1 + radius * 2), 0)
		self.center = Point(0, 0)
		self.half_size = Size(self.sight.size.width // 2, self.sight.size.height // 2)
	def is_visible(self, x, y):
		""" Returns True if cell at world coords is visible after last update(). """
		fov_pos = Point(self.half_size.width + x - self.center.x,
				  self.half_size.height + y - self.center.y,
				  )
		if not self.sight.valid(fov_pos):
			return False
		return self.sight.cell(fov_pos)
	def update(self, new_center, is_transparent):
		""" Updates FOV for given new center point.
		Uses is_transparent(Point):bool to determine if cells is transparent for sight.
		After that, function is_visible() can be used to check for each cell.
		"""
		self.center = new_center
		Log.debug('Recalculating Field Of View.')
		self.sight.clear(0)
		for pos in self.sight.size.iter_points():
			Log.debug('FOV pos: {0}'.format(pos))
			rel_pos = Point(
					self.half_size.width - pos.x,
					self.half_size.height - pos.y,
					)
			Log.debug('FOV rel pos: {0}'.format(rel_pos))
			if (float(rel_pos.x) / self.half_size.width) ** 2 + (float(rel_pos.y) / self.half_size.height) ** 2 > 1:
				continue
			Log.debug('Is inside FOV ellipse.')
			Log.debug('Traversing line of sight: [0;0] -> {0}'.format(rel_pos))
			for inner_line_pos in algorithm.bresenham(Point(0, 0), rel_pos):
				real_world_pos = self.center + inner_line_pos
				Log.debug('Line pos: {0}, real world pos: {1}'.format(inner_line_pos, real_world_pos))
				fov_pos = Point(self.half_size.width + inner_line_pos.x,
						self.half_size.height + inner_line_pos.y,
						)
				Log.debug('Setting as visible: {0}'.format(fov_pos))
				if not self.sight.cell(fov_pos):
					if real_world_pos.x >= 0 and real_world_pos.y >= 0:
						yield real_world_pos
					self.sight.set_cell(fov_pos, True)
				if not is_transparent(real_world_pos):
					Log.debug('Not passable, stop: {0}'.format(real_world_pos))
					break
		Log.debug("Full FOV:\n{0}".format(repr(self.sight)))
