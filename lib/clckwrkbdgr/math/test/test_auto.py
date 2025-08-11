from clckwrkbdgr import unittest
from .. import auto
from clckwrkbdgr.math import Point, Matrix, Size

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

class MockMap:
	def __init__(self, start_pos, matrix):
		self.pos = Point(start_pos)
		self.matrix = Matrix.fromstring(matrix)
	def move(self, step):
		self.pos += step

class MockAutoexplorer(auto.Autoexplorer):
	def __init__(self, plane):
		self.plane = plane
		super(MockAutoexplorer, self).__init__()
	def get_current_pos(self):
		return self.plane.pos
	def get_matrix(self):
		return self.plane.matrix
	def is_passable(self, pos):
		return self.plane.matrix.cell(pos) == '.'
	def is_valid_target(self, target):
		distance = target - self.get_current_pos()
		diff = abs(distance)
		if not (3 < diff.x < 10 or 3 < diff.y < 10):
			return False
		return True
	def target_area_size(self):
		return Size(21, 21)

class TestAutoExplorer(unittest.TestCase):
	@staticmethod
	def to_string(plane): # pragma: no cover
		result = []
		for y in range(plane.pos.y - 20, plane.pos.y + 20):
			result.append('')
			for x in range(plane.pos.x - 20, plane.pos.x + 20):
				if plane.pos == (x, y):
					result[-1] += '@'
				elif not plane.matrix.valid((x, y)):
					result[-1] += '~'
				else:
					result[-1] += plane.matrix.cell((x, y))
		return '\n'.join(result) + '\n'

	def setUp(self):
		self.plane = MockMap((10, 10), MAIN_TEST_MAP)
		self.autoexplore = MockAutoexplorer(self.plane)

	def step(self, expected=None):
		try:
			result = self.autoexplore.next()
			self.plane.move(result)
			if expected:
				self.assertEqual(result, expected)
		except: # pragma: no cover
			print(self.to_string(self.plane))
			raise

	@unittest.mock.patch('random.randrange')
	def should_wander(self, random_randrange):
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
