from ._base import Point
from ._base import get_neighbours

class Wave(object):
	""" Defines abstract wave algorithm on set of linkes nodes (like graph or matrix)
	from start until it reaches the target node.
	Calcultes path of nodes (including start and target) if possible.
	Create a subclass with specific implementation of abstract functions
	for specific functionality.
	>>> wave = CustomWave(start, stop)
	>>> path = wave.run()
	"""
	def is_linked(self, node_from, node_to): # pragma: no cover
		""" Should return True if node_to is directly reachable from node_from.
		Allows directional graphs when function is_linked(from, to) !== is_linked(to, from).
		"""
		raise NotImplementedError
	def get_links(self, node): # pragma: no cover
		""" Should return iterable of all nodes directly reachable from given node. """
		raise NotImplementedError
	def reorder_links(self, previous_node, links): # pragma: no cover
		""" Could reorder found links by priority if needed.
		First link will be used when constructing the final path.
		Does nothing by default.
		"""
		return links
	def run(self, start, target, depth=10000):
		""" Parameter depth serves as safeguard. After that number of waves algorithm
		gives up if target is not reached yet and returns None.
		If target is callable, it should receive a wave (list of Points) and return
		a Point that could be considired as target (or None to continue exploring).
		"""
		waves = [{start}]
		already_used = set()
		if callable(target):
			find_target = target
		else:
			find_target = lambda _wave: (target if target in _wave else None)
		while depth > 0:
			depth -= 1
			closest = set(node for previous in waves[-1] for node in self.get_links(previous))
			new_wave = closest - already_used
			if not new_wave:
				return None
			found_target = find_target(new_wave)
			if found_target:
				path = [found_target]
				for wave in reversed(waves):
					path.insert(0, next(node for node in self.reorder_links(path[0], wave) if self.is_linked(node, path[0])))
				return path
			already_used |= new_wave
			waves.append(new_wave)
		return None

class MatrixWave(Wave):
	""" Searches for the shortest path in matrix of cells.
	Redefine is_passable() to specify passability of cells.
	"""
	def __init__(self, matrix, region=None):
		""" Starts wave in given matrix with optional region
		(by default uses full matrix).
		"""
		self.matrix = matrix
		self.region = region
	def is_linked(self, node_from, node_to):
		distance = abs(node_from - node_to)
		return distance.x <= 1 and distance.y <= 1
	def reorder_links(self, previous_node, links):
		return sorted(links, key=lambda p: sum(abs(previous_node - p)))
	def is_passable(self, point, orig_point): # pragma: no cover
		""" Should return True if cell at point is passable
		if movement is originated from orig_point.
		"""
		raise NotImplementedError()
	def get_links(self, node):
		return [p for p in get_neighbours(
			self.matrix, node,
			with_diagonal=True,
			)
			 if self.is_passable(p, node)
			 and (self.region is None or self.region.contains(p, with_border=True))
			 ]

def floodfill(start, spread_function):
	""" Fills area starting from 'start' and using spread_function(p) to iterate over next possible points to advance.
	Does not check if start is already 'filled', it should be checked by caller or spread_function.
	Yields generated values.
	"""
	already_affected = {start}
	last_wave = {start}
	yield start
	while last_wave:
		wave = set()
		for point in last_wave:
			wave |= set(spread_function(point))
		for point in wave - already_affected:
			yield point
		already_affected |= wave
		last_wave = wave

def bresenham(start, stop):
	""" Bresenham's algorithm.
	Yields points between start and stop (including).
	"""
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
