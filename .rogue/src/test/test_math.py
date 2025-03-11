import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
import clckwrkbdgr.math
from ..math import Point, Size, Rect, Matrix
from ..math import distance
from ..math import bresenham
from ..math import find_path
from ..math import FieldOfView, in_line_of_sight

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

class TestMapAlgorithms(unittest.TestCase):
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
		path = find_path(
				matrix, Point(17, 4),
				is_passable=lambda p, _from: matrix.cell(p) == '.',
				find_target=lambda wave: target if target in wave else None,
				)
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

		is_diagonal = lambda p, _from: abs(p.x - _from.x) + abs(p.y - _from.y) == 2
		path = find_path(
				matrix, Point(17, 4),
				is_passable=lambda p, _from: matrix.cell(p) == '.' and not is_diagonal(p, _from),
				find_target=lambda wave: target if target in wave else None,
				)
		for p in path:
			matrix.set_cell(p, '*')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#***#....#***#######
				#.#*####.#*#*****..#
				#.#*...#***#.###*..#
				#.#*...#*###.###**.#
				#.#******#.........#
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
		path = find_path(
				matrix, Point(17, 4),
				is_passable=lambda p, _from: matrix.cell(p) == '.',
				find_target=lambda wave: target if target in wave else None,
				)
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
		path = find_path(
				matrix, Point(17, 4),
				is_passable=lambda p, _from: matrix.cell(p) != '#',
				find_target=lambda wave: next((target for target in wave
				if any(
					matrix.cell(p) == ' '
					for p in clckwrkbdgr.math.get_neighbours(matrix, target, with_diagonal=True)
					)
				), None),
				)
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
	def should_calculate_field_of_view(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            #     #
				#                  #
				#                  #
				####################
				""").replace('\n', ''))
		fov = FieldOfView(3)
		for p in fov.update(Point(11, 2), is_transparent=lambda p: matrix.valid(p) and matrix.cell(p) != '#'):
			if matrix.cell(p) == '#':
				matrix.set_cell(p, '%')
			else:
				matrix.set_cell(p, '.')
		self.assertTrue(fov.is_visible(11, 2))
		self.assertTrue(fov.is_visible(12, 2))
		self.assertTrue(fov.is_visible(12, 2))
		self.assertFalse(fov.is_visible(14, 3))
		self.assertTrue(fov.is_visible(14, 2))
		self.assertFalse(fov.is_visible(15, 2))
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				#########%%%%%######
				#        .....     #
				#       .......    #
				#        ....%     #
				#        .....     #
				#          .       #
				####################
				"""))
	def should_calculate_field_of_view_in_absolute_darkness(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            #     #
				#                  #
				#                  #
				####################
				""").replace('\n', ''))
		fov = FieldOfView(3)
		source = Point(11, 2)
		for p in fov.update(Point(11, 2), is_transparent=lambda p: max(abs(source.x - p.x), abs(source.y - p.y)) < 1):
			matrix.set_cell(p, '.')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#         ...      #
				#         ...      #
				#         ...#     #
				#                  #
				#                  #
				####################
				"""))
	def should_check_direct_line_of_sight(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            ###   #
				#            #     #
				#                  #
				####################
				""").replace('\n', ''))
		source = Point(11, 2)
		is_transparent=lambda p: matrix.valid(p) and matrix.cell(p) not in '#*'
		for p in matrix.size.iter_points():
			if in_line_of_sight(source, p, is_transparent):
				if matrix.cell(p) == '#':
					matrix.set_cell(p, '*')
				else:
					matrix.set_cell(p, '.')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				########*******#####
				*..................*
				*..................*
				*............*##   #
				*............*     #
				*.............     #
				####**********######
				"""))
