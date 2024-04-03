import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from ..math import Point, Size, Rect, Matrix

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
