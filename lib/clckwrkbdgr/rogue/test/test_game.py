import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from ..math import Point, Size
from ..pcg._base import RNG
from ..pcg import builders
from .. import pcg
from .. import game

class MockCell(game.Cell):
	def __init__(self, *args, **kwargs):
		visited = False
		if 'visited' in kwargs:
			visited = kwargs['visited']
			del kwargs['visited']
		super(MockCell, self).__init__(*args, **kwargs)
		self.visited = visited

class StrBuilder(builders.Builder):
	""" Set ._map_data to multiline string (one char for each cell).
	Register cell types according to those chars.
	Set char to '@' to indicate start pos.
	"""
	def _build(self):
		self._map_data = self._map_data.splitlines()
		for x in range(self.size.width):
			for y in range(self.size.height):
				self.strata.set_cell(x, y, self._map_data[y][x])
				if self._map_data[y][x] == '@':
					self.start_pos = Point(x, y)

class MockBuilder(builders.Builder):
	def _build(self):
		for x in range(self.size.width):
			self.strata.set_cell(x, 0, 'wall')
			self.strata.set_cell(x, self.size.height - 1, 'wall')
		for y in range(self.size.height):
			self.strata.set_cell(0, y, 'wall')
			self.strata.set_cell(self.size.width - 1, y, 'wall')
		for x in range(1, self.size.width - 1):
			for y in range(1, self.size.height - 1):
				self.strata.set_cell(x, y, 'floor')
		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) == 'floor'
		obstacle_pos = pcg.pos(self.rng, self.size, floor_only)
		self.strata.set_cell(obstacle_pos.x, obstacle_pos.y, 'wall')

		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		self.exit_pos = pcg.pos(self.rng, self.size, floor_only)

		# Room.
		room_pos = pcg.pos(self.rng, Size(self.size.width - 6, self.size.height - 5), floor_only)
		room_width = self.rng.range(3, 5)
		room_height = self.rng.range(3, 4)
		for x in range(room_width):
			self.strata.set_cell(room_pos.x + x, room_pos.y + 0, 'wall_h')
			self.strata.set_cell(room_pos.x + x, room_pos.y + room_height - 1, 'wall_h')
		for y in range(room_height):
			self.strata.set_cell(room_pos.x + 0, room_pos.y + y, 'wall_v')
			self.strata.set_cell(room_pos.x + room_width - 1, room_pos.y + y, 'wall_v')
		for x in range(1, room_width - 1):
			for y in range(1, room_height - 1):
				self.strata.set_cell(room_pos.x + x, room_pos.y + y, 'water')
		self.strata.set_cell(room_pos.x, room_pos.y, 'corner')
		self.strata.set_cell(room_pos.x, room_pos.y + room_height - 1, 'corner')
		self.strata.set_cell(room_pos.x + room_width - 1, room_pos.y, 'corner')
		self.strata.set_cell(room_pos.x + room_width - 1, room_pos.y + room_height - 1, 'corner')
		door_pos = self.rng.range(1, 4)
		self.strata.set_cell(room_pos.x + door_pos, room_pos.y, 'door')

class TestDungeon(unittest.TestCase):
	def should_build_dungeon(self):
		rng = RNG(0)
		builder = game.build_dungeon(MockBuilder, rng, Size(20, 20))
		self.assertEqual(builder.start_pos, Point(9, 12))
		self.assertEqual(builder.exit_pos, Point(7, 16))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				####################
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#........+-++......#
				#........|~~|......#
				#.....#..+--+......#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				####################
				""")
		self.assertEqual(builder.strata.tostring(lambda c: c.sprite), expected)
	def should_autoexplore_map(self):
		rng = RNG(0)
		builder = StrBuilder(rng, Size(20, 10))
		builder._map_data = textwrap.dedent("""\
				####################
				#........#.##......#
				#........#..#......#
				#....##.!$$!$!.....#
				#....#!!!!!!!!!....#
				#....$!!!!!!!!!....#
				#....!!!!@!!!!!....#
				#....!!!!!!!!!!....#
				#.....!!!!!!!!!....#
				####################
				""")
		builder.add_cell_type(None, game.Cell, ' ', False)
		builder.add_cell_type('#', MockCell, "#", False, remembered='+')
		builder.add_cell_type('$', MockCell, "$", False, remembered='+', visited=True)
		builder.add_cell_type('.', MockCell, ".", True)
		builder.add_cell_type('!', MockCell, ".", True, visited=True)
		builder.add_cell_type('@', MockCell, ".", True, visited=True)
		builder.build()

		path = game.autoexplore(builder.start_pos, builder.strata)
		self.assertEqual(path, [
			Point(x=9, y=6), Point(x=8, y=5), Point(x=7, y=4),
			])
