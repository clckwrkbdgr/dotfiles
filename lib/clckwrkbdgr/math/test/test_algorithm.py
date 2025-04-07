from clckwrkbdgr import unittest
import textwrap
import clckwrkbdgr.math
from clckwrkbdgr.math import algorithm, Matrix, Point, Size
from clckwrkbdgr.math.algorithm import bresenham

class TestMatrix(unittest.TestCase):
	def should_flood_fill_area(self):
		matrix = Matrix.fromstring(textwrap.dedent("""\
		#########
		# #   # #
		# # # # #
		#   # ###
		# # #   #
		#########
		"""))
		area = algorithm.floodfill(Point(1, 1), spread_function=lambda p: [x for x in clckwrkbdgr.math.get_neighbours(matrix, p) if matrix.cell(x) == ' '])
		for point in area:
			matrix.set_cell(point, '.')

		expected = Matrix.fromstring(textwrap.dedent("""\
		#########
		#.#...# #
		#.#.#.# #
		#...#.###
		#.#.#...#
		#########
		"""))
		self.assertEqual(matrix, expected, msg='\n{0}vs\n{1}'.format(matrix.tostring(), expected.tostring()))

class TestWavePathfinder(unittest.TestCase):
	class _CustomWave(algorithm.Wave):
		def __init__(self, matrix):
			self.matrix = matrix
		def get_links(self, pos):
			return clckwrkbdgr.math.get_neighbours(self.matrix, pos, check=lambda cell: cell != '#')
		def is_linked(self, pos_from, pos_to):
			return pos_to in self.get_links(pos_from)

	def should_find_path(self):
		matrix = Matrix.fromstring(textwrap.dedent("""\
		#########
		#<#567  #
		#0#4#8# #
		#123#9###
		# # #ab>#
		#########
		"""))
		wave = self._CustomWave(matrix)
		path = wave.run(next(matrix.find('<')), next(matrix.find('>')))
		expected = [(p, matrix.cell(p)) for p in matrix.keys() if matrix.cell(p) not in ('#', ' ')]
		expected = sorted(expected, key=lambda p: -1 if p[1] == '<' else (10000 if p[1] == '>' else ord(p[1])))
		expected = [p for p, c in expected]
		self.assertEqual(path, expected)
	def should_not_find_path_when_target_is_out_of_reach(self):
		matrix = Matrix.fromstring(textwrap.dedent("""\
		#########
		#<#     #
		# # # # #
		#   # ###
		# # # #>#
		#########
		"""))
		wave = self._CustomWave(matrix)
		path = wave.run(next(matrix.find('<')), next(matrix.find('>')))
		self.assertIsNone(path)
	def should_not_give_up_if_path_was_not_found_soon(self):
		matrix = Matrix.fromstring(textwrap.dedent("""\
		#########
		#<#     #
		# # # # #
		#   # ###
		# # #  >#
		#########
		"""))
		wave = self._CustomWave(matrix)
		path = wave.run(next(matrix.find('<')), next(matrix.find('>')), depth=3)
		self.assertIsNone(path)

class TestMatrixWave(unittest.TestCase):
	class _CustomWave(algorithm.MatrixWave):
		def is_passable(self, p, _):
			return self.matrix.cell(p) == '.'
	class _CustomExploreWave(algorithm.MatrixWave):
		def is_passable(self, p, _):
			return self.matrix.cell(p) != '#'

	class _CustomNonDiagonalWave(algorithm.MatrixWave):
		def is_diagonal(self, p, _from):
			return abs(p.x - _from.x) + abs(p.y - _from.y) == 2
		def is_passable(self, p, _from):
			return self.matrix.cell(p) == '.' and not self.is_diagonal(p, _from)

	def should_find_path_in_matrix(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#...#....#...#######
				#.#.####.#.#.......#
				#.#....#...#.###...#
				#.#....#.###.###...#
				#.#......#.........#
				####################
				""").replace('\n', ''))
		target = Point(1, 1)
		wave = self._CustomWave(matrix)
		path = wave.run(Point(17, 4), target)
		for p in path:
			matrix.set_cell(p, '*')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#**.#....#.**#######
				#.#*####.#*#.***...#
				#.#.**.#.*.#.###*..#
				#.#...*#*###.###.*.#
				#.#....*.#.........#
				####################
				"""))
	def should_find_path_in_matrix_without_diagonal_shifts(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#...#....#...#######
				#.#.####.#.#.......#
				#.#....#...#.###...#
				#.#....#.###.###...#
				#.#......#.........#
				####################
				""").replace('\n', ''))
		target = Point(1, 1)

		wave = self._CustomNonDiagonalWave(matrix)
		path = wave.run(Point(17, 4), target)
		for p in path:
			matrix.set_cell(p, '*')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#***#....#***#######
				#.#*####.#*#*****..#
				#.#*...#***#.###*..#
				#.#**..#*###.###**.#
				#.#.*****#.........#
				####################
				"""))
	def should_not_find_path_in_matrix_if_exit_is_closed(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#...#....#...#######
				#.#.####.#.#.......#
				#.#....#...#.###...#
				#.#....#.###.###...#
				#.#....#.#.........#
				####################
				""").replace('\n', ''))
		target = Point(1, 1)
		wave = self._CustomWave(matrix)
		path = wave.run(Point(17, 4), target)
		self.assertIsNone(path)
	def should_find_path_in_matrix_to_the_first_fit_target(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#   #    #...#######
				# # #### #.#.......#
				# #    # ..#.###...#
				# #    # ###.###...#
				# #      #.........#
				####################
				""").replace('\n', ''))
		target = Point(1, 1)
		wave = self._CustomExploreWave(matrix)
		find_target = lambda wave: next((target for target in wave
			  if any(
				  matrix.cell(p) == ' '
				  for p in clckwrkbdgr.math.get_neighbours(matrix, target, with_diagonal=True)
				  )
			  ), None)
		path = wave.run(Point(17, 4), find_target)
		for p in path:
			matrix.set_cell(p, '*')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#   #    #.**#######
				# # #### #*#.***...#
				# #    # *.#.###*..#
				# #    # ###.###.*.#
				# #      #.........#
				####################
				"""))

class TestGeometry(unittest.TestCase):
	def should_generate_bresenham_lines(self):
		self.assertEqual(list(bresenham(Point(0, 0), Point(3, 9))), [Point(*x) for x in [
			(0,0), (0,1), (1,2), (1,3), (1,4), (2,5), (2,6), (2,7), (3,8), (3,9),
			]])
		self.assertEqual(list(bresenham(Point(0, 0), Point(3, 10))), [Point(*x) for x in [
			(0,0), (0,1), (1,2), (1,3), (1,4), (2,5), (2,6), (2,7), (2,8), (3,9), (3, 10),
			]])
		self.assertEqual(list(bresenham(Point(0, 0), Point(9, 3))), [Point(*x) for x in [
			(0,0), (1,0), (2,1), (3,1), (4,1), (5,2), (6,2), (7,2), (8,3), (9,3),
			]])
		self.assertEqual(list(bresenham(Point(0, 0), Point(9, 9))), [Point(*x) for x in [
			(0,0), (1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7), (8,8), (9,9),
			]])
		self.assertEqual(list(bresenham(Point(0, 0), Point(9, 0))), [Point(*x) for x in [
			(0,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0),
			]])
		self.assertEqual(list(bresenham(Point(0, 0), Point(0, 9))), [Point(*x) for x in [
			(0,0), (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7), (0,8), (0,9),
			]])
