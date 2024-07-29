from collections import namedtuple
import copy
import itertools
from .messages import Log

_Point = namedtuple('Point', 'x y')
class Point(_Point):
	def __add__(self, other):
		return Point(self.x + other.x, self.y + other.y)
	def __mul__(self, factor):
		return Point(self.x * factor, self.y * factor)
	def __sub__(self, other):
		return Point(self.x - other.x, self.y - other.y)

_Size = namedtuple('Size', 'width height')
class Size(_Size):
	def __iter__(self):
		return itertools.chain.from_iterable((Point(x, y) for x in range(self.width)) for y in range(self.height))

_Rect = namedtuple('Rect', 'topleft size')
class Rect(_Rect):
	def contains(self, pos):
		return self.topleft.x <= pos.x < (self.topleft.x + self.size.width) and self.topleft.y <= pos.y < (self.topleft.y + self.size.height)

class Matrix:
	__slots__ = ['cells', 'size']
	def __init__(self, size, default_value=None):
		self.size = size
		self.clear(default_value)
	def __repr__(self):
		result = 'Matrix({0}, [\n'.format(self.size)
		result += self.tostring(indent='\t') + '\t])'
		return result
	def tostring(self, cell_str=None, indent=''):
		cell_str = cell_str or str
		result = ''
		for index, c in enumerate(self.cells):
			if index % self.size.width == 0:
				if index:
					result += '\n'
				if indent:
					result += indent
			result += cell_str(c)
		result += '\n'
		return result
	def valid(self, pos):
		return 0 <= pos.x < self.size.width and 0 <= pos.y < self.size.height
	def set_cell(self, x, y, value):
		self.cells[x + y * self.size.width] = value
	def cell(self, x, y):
		return self.cells[x + y * self.size.width]
	def clear(self, value):
		self.cells = [copy.copy(value) for _ in range(self.size.width * self.size.height)]
	def get_neighbours(self, x, y, with_diagonal=False):
		neighbours = [
				Point(x + 1, y    ),
				Point(x    , y + 1),
				Point(x - 1, y    ),
				Point(x    , y - 1),
				]
		if with_diagonal:
			neighbours += [
					Point(x + 1, y + 1),
					Point(x - 1, y + 1),
					Point(x + 1, y - 1),
					Point(x - 1, y - 1),
					]
		for p in neighbours:
			if not self.valid(p):
				continue
			yield p

def bresenham(start, stop):
	dx = abs(stop.x - start.x)
	sx = 1 if start.x < stop.x else -1
	dy = -abs(stop.y - start.y)
	sy = 1 if start.y < stop.y else -1
	error = dx + dy
	
	x, y = start.x, start.y
	while True:
		yield Point(x, y)
		if x == stop.x and y == stop.y:
			break
		e2 = 2 * error
		if e2 >= dy:
			if x == stop.x: # pragma: no cover -- safeguard, should not be reached.
				break
			error = error + dy
			x += sx
		if e2 <= dx:
			if y == stop.y: # pragma: no cover -- safeguard, should not be reached.
				break
			error = error + dx
			y += sy

def find_path(matrix, start, is_passable, find_target):
	""" Searches for the shortest path on matrix of cells
	from start point until find_target in new wave.
	is_passable(point, orig_point) should return True if cell is passable when moving from orig_point.
	find_traget(set of points) should return point which could serve as stop, otherwise None.
	"""
	def _reorder_links(_previous_node, _links):
		return sorted(_links, key=lambda p: abs(_previous_node.x - p.x) + abs(_previous_node.y - p.y))
	def _is_linked(_node_from, _node_to):
		return abs(_node_from.x - _node_to.x) <= 1 and abs(_node_from.y - _node_to.y) <= 1
	def _get_links(_node):
		return [p for p in matrix.get_neighbours(
			_node.x, _node.y,
			with_diagonal=True,
			)
			 if is_passable(p, _node)
			 ]
	waves = [{start}]
	already_used = set()
	depth = matrix.size.width * matrix.size.width * matrix.size.height * matrix.size.height
	while depth > 0:
		depth -= 1
		closest = set(node for previous in waves[-1] for node in _get_links(previous))
		new_wave = closest - already_used
		if not new_wave:
			return None
		target = find_target(sorted(new_wave))
		if target:
			path = [target]
			for wave in reversed(waves):
				path.insert(0, next(node for node in _reorder_links(path[0], sorted(wave)) if _is_linked(node, path[0])))
			return path
		already_used |= new_wave
		waves.append(new_wave)

class FieldOfView:
	def __init__(self, radius):
		self.sight = Matrix(Size(1 + radius * 2, 1 + radius * 2), 0)
		self.center = Point(0, 0)
		self.half_size = Size(self.sight.size.width // 2, self.sight.size.height // 2)
	def is_visible(self, x, y):
		fov_pos = Point(self.half_size.width + x - self.center.x,
				  self.half_size.height + y - self.center.y,
				  )
		if not self.sight.valid(fov_pos):
			return False
		return self.sight.cell(fov_pos.x, fov_pos.y)
	def update(self, new_center, is_transparent):
		self.center = new_center
		Log.debug('Recalculating Field Of View.')
		self.sight.clear(0)
		for pos in self.sight.size:
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
			for inner_line_pos in bresenham(Point(0, 0), rel_pos):
				real_world_pos = self.center + inner_line_pos
				Log.debug('Line pos: {0}, real world pos: {1}'.format(inner_line_pos, real_world_pos))
				fov_pos = Point(self.half_size.width + inner_line_pos.x,
						self.half_size.height + inner_line_pos.y,
						)
				Log.debug('Setting as visible: {0}'.format(fov_pos))
				if not self.sight.cell(fov_pos.x, fov_pos.y):
					yield real_world_pos
					self.sight.set_cell(fov_pos.x, fov_pos.y, True)
				if not is_transparent(real_world_pos):
					Log.debug('Not passable, stop: {0}'.format(real_world_pos))
					break
		Log.debug("Full FOV:\n{0}".format(repr(self.sight)))
