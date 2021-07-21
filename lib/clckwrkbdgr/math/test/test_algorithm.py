import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
import clckwrkbdgr.math
from clckwrkbdgr.math import algorithm, Matrix, Point

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
	class MatrixWave(algorithm.Wave):
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
		wave = self.MatrixWave(matrix)
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
		wave = self.MatrixWave(matrix)
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
		wave = self.MatrixWave(matrix)
		path = wave.run(next(matrix.find('<')), next(matrix.find('>')), depth=3)
		self.assertIsNone(path)
