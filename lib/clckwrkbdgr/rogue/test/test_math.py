import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from ..math import Point, Size, Rect, Matrix
from ..math import bresenham
from ..math import find_path
from ..math import FieldOfView

class TestPoint(unittest.TestCase):
	def should_add_two_point_values(self):
		a = Point(1, 2)
		b = Point(5, 8)
		self.assertEqual(a + b, Point(6, 10))
	def should_subtract_two_point_values(self):
		a = Point(1, 2)
		b = Point(5, 8)
		self.assertEqual(a - b, Point(-4, -6))
	def should_multiply_point_values(self):
		a = Point(1, 2)
		self.assertEqual(a * 2, Point(2, 4))

class TestRect(unittest.TestCase):
	def should_detect_containing_points(self):
		rect = Rect(Point(1, 2), Size(4, 5))
		self.assertFalse(rect.contains(Point(0, 0)))
		self.assertTrue (rect.contains(Point(1, 2)))
		self.assertTrue (rect.contains(Point(1, 3)))
		self.assertTrue (rect.contains(Point(2, 3)))
		self.assertTrue (rect.contains(Point(3, 4)))
		self.assertTrue (rect.contains(Point(4, 5)))

class TestSize(unittest.TestCase):
	def should_iter_over_size(self):
		size = Size(2, 3)
		self.assertEqual(list(size), [
			Point(0, 0), Point(1, 0),
			Point(0, 1), Point(1, 1),
			Point(0, 2), Point(1, 2),
			])

class TestMatrix(unittest.TestCase):
	def should_create_matrix_with_default_value(self):
		matrix = Matrix(Size(2, 3), '.')
		self.assertEqual(matrix.cells, ['.', '.', '.', '.', '.', '.'])
	def should_repr_matrix_as_string(self):
		matrix = Matrix(Size(2, 3), '.')
		self.assertEqual(repr(matrix), 'Matrix(Size(width=2, height=3), [\n\t..\n\t..\n\t..\n\t])')
	def should_define_valid_points(self):
		matrix = Matrix(Size(2, 3), '.')
		self.assertTrue(matrix.valid(Point(0, 0)))
		self.assertTrue(matrix.valid(Point(1, 2)))
		self.assertFalse(matrix.valid(Point(-1, -1)))
		self.assertFalse(matrix.valid(Point(4, 1)))
		self.assertFalse(matrix.valid(Point(1, 5)))
	def should_set_and_get_cells(self):
		matrix = Matrix(Size(2, 3), '.')
		matrix.set_cell(0, 1, '#')
		self.assertEqual(matrix.cell(0, 0), '.')
		self.assertEqual(matrix.cell(0, 1), '#')
		self.assertEqual(matrix.cells, ['.', '.', '#', '.', '.', '.'])
	def should_clear_matrix_and_fill_with_new_value(self):
		matrix = Matrix(Size(2, 3), '.')
		matrix.clear('#')
		self.assertEqual(matrix.cells, ['#', '#', '#', '#', '#', '#'])
	def should_get_valid_neighbours(self):
		matrix = Matrix(Size(4, 5), '.')
		self.assertEqual(list(matrix.get_neighbours(0, 0)), [
			Point(x=1, y=0), Point(x=0, y=1)
			])
		self.assertEqual(list(matrix.get_neighbours(0, 0, with_diagonal=True)), [
			Point(x=1, y=0), Point(x=0, y=1), Point(x=1, y=1)
			])
		self.assertEqual(list(matrix.get_neighbours(2, 0)), [
			Point(x=3, y=0), Point(x=2, y=1), Point(x=1, y=0)
			])
		self.assertEqual(list(matrix.get_neighbours(2, 0, with_diagonal=True)), [
			Point(x=3, y=0), Point(x=2, y=1), Point(x=1, y=0), Point(x=3, y=1), Point(x=1, y=1)
			])
		self.assertEqual(list(matrix.get_neighbours(0, 2)), [
			Point(x=1, y=2), Point(x=0, y=3), Point(x=0, y=1)
			])
		self.assertEqual(list(matrix.get_neighbours(0, 2, with_diagonal=True)), [
			Point(x=1, y=2), Point(x=0, y=3), Point(x=0, y=1), Point(x=1, y=3), Point(x=1, y=1)
			])
		self.assertEqual(list(matrix.get_neighbours(2, 2)), [
			Point(x=3, y=2), Point(x=2, y=3), Point(x=1, y=2), Point(x=2, y=1)
			])
		self.assertEqual(list(matrix.get_neighbours(2, 2, with_diagonal=True)), [
			Point(x=3, y=2), Point(x=2, y=3), Point(x=1, y=2), Point(x=2, y=1), Point(x=3, y=3), Point(x=1, y=3), Point(x=3, y=1), Point(x=1, y=1)
			])

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
		matrix.cells = list(textwrap.dedent("""\
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
				is_passable=lambda p: matrix.cell(p.x, p.y) == '.',
				find_target=lambda wave: target if target in wave else None,
				)
		for p in path:
			matrix.set_cell(p.x, p.y, '*')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#**.#....#.**#######
				#.#*####.#*#.***...#
				#.#.**.#.*.#.###*..#
				#.#...*#*###.###.*.#
				#.#....*.#.........#
				####################
				"""))
	def should_not_find_path_in_matrix_if_exit_is_closed(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.cells = list(textwrap.dedent("""\
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
				is_passable=lambda p: matrix.cell(p.x, p.y) == '.',
				find_target=lambda wave: target if target in wave else None,
				)
		self.assertIsNone(path)
	def should_find_path_in_matrix_to_the_first_fit_target(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.cells = list(textwrap.dedent("""\
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
				is_passable=lambda p: matrix.cell(p.x, p.y) != '#',
				find_target=lambda wave: next((target for target in wave
				if any(
					matrix.cell(p.x, p.y) == ' '
					for p in matrix.get_neighbours(target.x, target.y, with_diagonal=True)
					)
				), None),
				)
		for p in path:
			matrix.set_cell(p.x, p.y, '*')
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
		matrix.cells = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            #     #
				#                  #
				#                  #
				####################
				""").replace('\n', ''))
		fov = FieldOfView(3)
		for p in fov.update(Point(11, 2), is_visible=lambda p: matrix.valid(p) and matrix.cell(p.x, p.y) != '#'):
			if not matrix.valid(p):
				continue
			if matrix.cell(p.x, p.y) == '#':
				matrix.set_cell(p.x, p.y, '%')
			else:
				matrix.set_cell(p.x, p.y, '.')
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
