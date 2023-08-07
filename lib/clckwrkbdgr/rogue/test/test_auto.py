from ... import logging
from ... import unittest
from ..dungeon import Dungeon
from .. import auto

class MockDungeon(Dungeon):
	pass

class MockBuilder:
	def __init__(self, rogue_pos=None, maps=None):
		self.rogue_pos = rogue_pos or (0, 0)
		self.maps = maps
	def build_block(self, block):
		layout = self.maps.pop(0)
		for y, line in enumerate(layout.splitlines()):
			for x, cell in enumerate(line):
				block.set_cell((x, y), cell)
	def place_rogue(self, terrain):
		return self.rogue_pos

EMPTY_MAP = '\n'.join(["." * 32] * 32)
MAIN_TEST_MAP = unittest.dedent("""\
		.123456789.123456789.123456789..
		1..............................1
		2..............................2
		3..............................3
		4..............................4
		5..............................5
		6..............................6
		7..............................7
		8..............................8
		9..............................9
		................................
		1..............................1
		2..............................2
		3..............................3
		4..............................4
		5...............#####..........5
		6...................#..........6
		7.............#######..........7
		8...............#...#..........8
		9.................#.#..........9
		...............######...........
		1..............................1
		2..............................2
		3..............................3
		4..............................4
		5..............................5
		6..............................6
		7..............................7
		8..............................8
		9..............................9
		................................
		.123456789.123456789.123456789..
		""")

class TestAutoExplorer(unittest.TestCase):
	@staticmethod
	def to_string(dungeon): # pragma: no cover
		result = []
		for y in range(-20, 20):
			result.append('')
			for x in range(-20, 20):
				result[-1] += dungeon.get_sprite((x, y))
		return '\n'.join(result) + '\n'

	def setUp(self):
		builder = MockBuilder(rogue_pos=(10, 10), maps=[
			EMPTY_MAP, EMPTY_MAP, EMPTY_MAP,
			EMPTY_MAP, MAIN_TEST_MAP, EMPTY_MAP,
			EMPTY_MAP, EMPTY_MAP, EMPTY_MAP,
			])
		self.dungeon = MockDungeon(builder=builder)
		self.autoexplore = auto.Autoexplorer()

	def step(self, expected=None):
		try:
			result = self.autoexplore.process(self.dungeon)
			self.dungeon.control(result)
			if expected:
				self.assertEqual(result, expected)
		except: # pragma: no cover
			print(self.to_string(self.dungeon))
			raise

	@unittest.mock.patch('random.randrange')
	def should_generate_random_dungeon(self, random_randrange):
		random_randrange.side_effect = [
				15, 15,
				]

		self.step((1, 1))
		self.step((1, 1))
		self.step((1, 1))
		self.step((1, 1))
		self.step((1, 1))

		random_randrange.side_effect = [
				20, 20, # Not passable.
				16, 16, # Too close.
				25, 25, # Too far.
				19, 19,
				]
		self.step((-1, 1))
		self.step((-1, 1))
		self.step((1, 1))
		self.step((1, 1))
		self.step((1, 0))
		self.step((1, -1))
		self.step((1, 0))
	@unittest.mock.patch('random.randrange')
	def should_not_walk_in_old_directions(self, random_randrange):
		random_randrange.side_effect = [
				15, 10,
				]

		self.step((1, 0))
		self.step((1, 0))
		self.step((1, 0))
		self.step((1, 0))
		self.step((1, 0))

		random_randrange.side_effect = [
				5, 10, # Old direction.
				5, 5, # Old direction.
				22, 13,
				26, 18,
				26, 23,
				26, 18, # Old direction.
				26, 28,
				]
		for _ in range(7): self.step()
		for _ in range(5): self.step()
		for _ in range(5): self.step()
		for _ in range(5): self.step()
