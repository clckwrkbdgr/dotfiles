from collections import namedtuple
import copy
import itertools

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
