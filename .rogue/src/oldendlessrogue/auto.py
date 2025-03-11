import random
import logging
trace = logging.getLogger('rogue')
from clckwrkbdgr.math import algorithm
from clckwrkbdgr.math import Point, Size, Rect, get_neighbours, sign

class DungeonWave(algorithm.Wave):
	def __init__(self, matrix, region):
		self.matrix = matrix
		self.region = region
	def is_linked(self, node_from, node_to):
		distance = abs(node_from - node_to)
		return distance.x <= 1 and distance.y <= 1
	def reorder_links(self, previous_node, links):
		return sorted(links, key=lambda p: sum(abs(previous_node - p)))
	def get_links(self, node):
		return [p for p in get_neighbours(
			self.matrix, node,
			with_diagonal=True,
			check=lambda c: c == '.'
			)
			 if self.region.contains(p, with_border=True)
			 ]

class Autoexplorer:
	def __init__(self):
		self.path = None
		self.previous_direction = None
	def process(self, dungeon):
		if self.path:
			direction = self.path.pop(0)
			self.previous_direction += direction
			return direction
		target = dungeon.rogue
		for _ in range(100):
			target = Point(
					random.randrange(dungeon.rogue.x - 10, dungeon.rogue.x + 10),
					random.randrange(dungeon.rogue.y - 10, dungeon.rogue.y + 10),
					)
			trace.debug('Autoexplorer target: trying {0}'.format(target))
			if dungeon.terrain.cell(target) != '.':
				trace.debug('Autoexplorer target: {0}: not passable'.format(target))
				continue
			distance = target - dungeon.rogue
			diff = abs(distance)
			direction = Point(sign(distance.x), sign(distance.y))
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
			if not(3 < diff.x < 10 or 3 < diff.y < 10):
				trace.debug('Autoexplorer target: too close or too far: {0}'.format(target))
				continue
			self.previous_direction = Point(0, 0)
			trace.debug('Autoexplorer target: good, picking {0}'.format(target))
			break
		wave = DungeonWave(dungeon.terrain, Rect(
			topleft=dungeon.rogue - Point(10, 10),
			size=Size(21, 21),
			))
		trace.debug('Autoexplorer forming path: {0} -> {1}'.format(dungeon.rogue, target))
		path = wave.run(dungeon.rogue, target)
		trace.debug('Autoexplorer wave: {0}'.format(path))
		self.path = list(b - a for a, b in zip(path, path[1:]))
		trace.debug('Autoexplorer sequence: {0}'.format(self.path))
		return self.process(None)
