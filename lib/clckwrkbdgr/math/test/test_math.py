from clckwrkbdgr import unittest
import json
try:
	import jsonpickle
except ImportError: # pragma: no cover
	jsonpickle = None
import textwrap
import clckwrkbdgr.math
from clckwrkbdgr.math import Point, Direction, distance, Size, Rect, Matrix

class MyVector(clckwrkbdgr.math.Vector):
	@property
	def first(self): return self.values[0]
	@first.setter
	def first(self, value): self.values[0] = value
	@property
	def second(self): return self.values[1]
	@second.setter
	def second(self, value): self.values[1] = value

class TestVector(unittest.TestCase):
	def should_create_vector(self):
		p = MyVector(1, 2)
		self.assertEqual(p.first, 1)
		self.assertEqual(p.second, 2)
		self.assertEqual(p[0], 1)
		self.assertEqual(p[1], 2)
		self.assertEqual(p, (1, 2))
	def should_call_setters(self):
		p = MyVector(1, 2)
		p.first = 2
		p.second = 3
		self.assertEqual(p[0], 2)
		self.assertEqual(p[1], 3)
	@unittest.skipUnless(jsonpickle, "Jsonpickle is not detected.")
	def should_serialize_vector_to_json(self): # pragma: no cover -- TODO needs mocks instead of just skipping.
		p = MyVector(1, 2)
		data = json.loads(jsonpickle.encode(p, unpicklable=False))
		self.assertEqual(data, [1, 2])
		self.assertEqual(jsonpickle.decode(jsonpickle.encode(p)), p)
	def should_have_hash(self):
		p = MyVector(1, 2)
		other = MyVector(1, 2)
		self.assertEqual(set([p]), set([other]))
	@unittest.skipUnless(jsonpickle, "Jsonpickle is not detected.")
	def should_deserialize_old_vector(self): # pragma: no cover -- TODO needs mocks instead of just skipping.
		q = jsonpickle.decode('{"py/newargs": {"py/tuple": [1, 2]}, "py/object": "clckwrkbdgr.math.test.test_math.MyVector", "py/seq": [1, 2]}')
		self.assertEqual(q.first, 1)
		self.assertEqual(q.second, 2)
	def should_create_vector_from_other_vector(self):
		p = MyVector(1, 2)
		o = MyVector(p)
		self.assertEqual(o.first, 1)
		self.assertEqual(o.second, 2)
	def should_compare_vectors(self):
		self.assertEqual(MyVector(1, 2), MyVector(1, 2))
		self.assertTrue(MyVector(1, 2) == MyVector(1, 2))
		self.assertFalse(MyVector(1, 2) != MyVector(1, 2))
		self.assertTrue(MyVector(1, 2) <= MyVector(1, 2))
		self.assertTrue(MyVector(1, 2) < MyVector(2, 2))
		self.assertTrue(MyVector(1, 2) < MyVector(1, 3))
	def should_get_absolute_values(self):
		self.assertEqual(abs(MyVector(1, 2)), MyVector(1, 2))
		self.assertEqual(abs(MyVector(-1, 2)), MyVector(1, 2))
		self.assertEqual(abs(MyVector(-1, -2)), MyVector(1, 2))
	def should_add_vectors(self):
		self.assertEqual(MyVector(1, 2) + MyVector(2, 3), MyVector(3, 5))
	def should_subtract_vectors(self):
		self.assertEqual(MyVector(3, 5) - MyVector(2, 3), MyVector(1, 2))
	def should_multiply_vector(self):
		self.assertEqual(MyVector(1, 2) * 2, MyVector(2, 4))
	def should_divide_vector(self):
		self.assertEqual(MyVector(2, 4) / 2, MyVector(1, 2))
		self.assertEqual(MyVector(5, 6) // 3, MyVector(1, 2))

class TestSize(unittest.TestCase):
	def should_iterate_over_point_within_size(self):
		size = Size(2, 2)
		indexes = ' '.join(''.join(map(str, index)) for index in size.iter_points())
		self.assertEqual(indexes, '00 10 01 11')

class TestPoint(unittest.TestCase):
	def should_yield_all_surrounding_neighbours(self):
		actual = set(Point(1, 2).neighbours())
		expected = set(map(Point, [
			(0, 1), (1, 1), (2, 1),
			(0, 2), (1, 2), (2, 2),
			(0, 3), (1, 3), (2, 3),
			]))
		self.assertEqual(actual, expected)
	def should_calculate_distance_between_two_points(self):
		self.assertEqual(distance(Point(0, 0), Point(0, 0)), 0)
		self.assertEqual(distance(Point(0, 0), Point(1, 0)), 1)
		self.assertEqual(distance(Point(0, 0), Point(1, 0)), 1)
		self.assertEqual(distance(Point(0, 0), Point(1, 1)), 1)
		self.assertEqual(distance(Point(0, 0), Point(2, 0)), 2)
		self.assertEqual(distance(Point(0, 0), Point(2, 1)), 2)
		self.assertEqual(distance(Point(0, 0), Point(2, 2)), 2)

class TestDirection(unittest.TestCase):
	def should_convert_shift_to_direction(self):
		self.assertEqual(Direction.from_points(Point(0, 0), Point(0, 0)), Direction.NONE)

		self.assertEqual(Direction.from_points(Point(0, 0), Point(1, 0)), Direction.RIGHT)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(-1, 0)), Direction.LEFT)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(0, 1)), Direction.DOWN)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(0, -1)), Direction.UP)

		self.assertEqual(Direction.from_points(Point(0, 0), Point(-1, 1)), Direction.DOWN_LEFT)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(1, -1)), Direction.UP_RIGHT)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(-1, -1)), Direction.UP_LEFT)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(1, 1)), Direction.DOWN_RIGHT)

		self.assertEqual(Direction.from_points(Point(0, 0), Point(2, 0)), Direction.RIGHT)
		self.assertEqual(Direction.from_points(Point(0, 0), Point(2, 3)), Direction.DOWN_RIGHT)

class TestRect(unittest.TestCase):
	def should_construct_rect(self):
		# 01234567890
		#0
		#1
		#2 ####
		#3 #  #
		#4 #  #
		#5 #  #
		#6 ####
		#7
		rect = Rect((1, 2), (4, 5))
		self.assertEqual(rect.topleft, Point(1, 2))
		self.assertEqual(rect.bottomright, Point(4, 6))
		self.assertEqual(rect.size, Point(4, 5))
		self.assertEqual(rect.width, 4)
		self.assertEqual(rect.height, 5)
		self.assertEqual(rect.top, 2)
		self.assertEqual(rect.left, 1)
		self.assertEqual(rect.bottom, 6)
		self.assertEqual(rect.right, 4)
	@unittest.skipUnless(jsonpickle, "Jsonpickle is not detected.")
	def should_serialize_rect(self): # pragma: no cover -- TODO needs mocks instead of just skipping.
		rect = Rect((1, 2), (4, 5))
		data = json.loads(jsonpickle.encode(rect, unpicklable=False))
		self.assertEqual(data, {'topleft': [1, 2], 'size' : [4, 5]})
		self.assertEqual(jsonpickle.decode(jsonpickle.encode(rect)), rect)
	def should_check_if_rects_are_equal(self):
		self.assertEqual(Rect((1, 2), (4, 5)), Rect((1, 2), (4, 5)))
		self.assertNotEqual(Rect((1, 2), (4, 5)), Rect((1, 2), (14, 15)))
	def should_detect_rect_containing_point(self):
		rect = Rect((1, 2), (4, 5))
		self.assertFalse(rect.contains(Point(0, 0)))
		self.assertFalse(rect.contains(Point(1, 2)))
		self.assertFalse(rect.contains(Point(1, 3)))
		self.assertTrue (rect.contains(Point(2, 3)))
		self.assertTrue (rect.contains(Point(3, 4)))
		self.assertFalse(rect.contains(Point(4, 5)))
		self.assertFalse(rect.contains(Point(0, 0), with_border=True))
		self.assertTrue (rect.contains(Point(1, 2), with_border=True))
		self.assertTrue (rect.contains(Point(1, 3), with_border=True))
		self.assertTrue (rect.contains(Point(2, 3), with_border=True))
		self.assertTrue (rect.contains(Point(3, 4), with_border=True))
		self.assertTrue (rect.contains(Point(4, 5), with_border=True))

class TestMatrix(unittest.TestCase):
	def should_create_matrix(self):
		m = Matrix((2, 3), default='*')
		self.assertEqual(m.size, (2, 3))
		self.assertEqual(m.width, 2)
		self.assertEqual(m.height, 3)
	def should_compare_matrices(self):
		a = Matrix((2, 3), default='*')
		with self.assertRaises(TypeError):
			a == 'something that is not matrix'
		b = Matrix((5, 6), default='*')
		self.assertNotEqual(a, b)

		a = Matrix.fromstring(textwrap.dedent("""\
				.X.
				XXX
				"""))
		b = Matrix.fromstring(textwrap.dedent("""\
				#.#
				.#.
				"""))
		c = Matrix.fromstring(textwrap.dedent("""\
				.X.
				XXX
				"""))
		self.assertNotEqual(a, b)
		self.assertEqual(a, c)
	def should_resize_matrix(self):
		m = Matrix((2, 3), default='*')
		self.assertEqual(m.size, (2, 3))
		m.resize((3, 2), default='_')
		self.assertEqual(m.size, (3, 2))
	def should_create_matrix_from_other_matrix(self):
		original = Matrix((2, 2))
		original.set_cell((0, 0), 'a')
		original.set_cell((0, 1), 'b')
		original.set_cell((1, 0), 'c')
		original.set_cell((1, 1), 'd')

		copy = Matrix(original)
		self.assertEqual(copy.cell((0, 0)), 'a')
		self.assertEqual(copy.cell((0, 1)), 'b')
		self.assertEqual(copy.cell((1, 0)), 'c')
		self.assertEqual(copy.cell((1, 1)), 'd')

		copy.set_cell((0, 0), '*')
		self.assertEqual(original.cell((0, 0)), 'a')

		original.set_cell((0, 0), '#')
		self.assertEqual(copy.cell((0, 0)), '*')
	def should_recognize_invalid_coords(self):
		m = Matrix((2, 2), default='*')
		self.assertTrue(m.valid((0, 0)))
		self.assertTrue(m.valid((0, 1)))
		self.assertTrue(m.valid((1, 0)))
		self.assertTrue(m.valid((1, 1)))
		self.assertFalse(m.valid((2, 2)))
		self.assertFalse(m.valid((-1, 0)))
	def should_get_cell_value(self):
		m = Matrix((2, 2), default='*')
		self.assertEqual(m.cell((0, 0)), '*')
		with self.assertRaises(KeyError):
			m.cell((-1, -1))
		with self.assertRaises(KeyError):
			m.cell((1, 10))
	def should_set_cell_value(self):
		m = Matrix((2, 2), default=' ')
		m.set_cell((0, 0), '*')
		self.assertEqual(m.cell((0, 0)), '*')
		with self.assertRaises(KeyError):
			m.set_cell((-1, -1), 'a')
		with self.assertRaises(KeyError):
			m.set_cell((1, 10), 'a')
	def should_iterate_over_indexes(self):
		m = Matrix((2, 2))
		m.data = list('abcd')
		indexes = ' '.join(''.join(map(str, index)) for index in m)
		self.assertEqual(indexes, '00 10 01 11')
		indexes = ' '.join(''.join(map(str, index)) for index in m.keys())
		self.assertEqual(indexes, '00 10 01 11')
		values = ' '.join(m.values())
		self.assertEqual(values, 'a b c d')
	def should_find_value_in_matrix(self):
		a = Matrix.fromstring(textwrap.dedent("""\
				ab
				ca
				"""))
		self.assertEqual(list(a.find('a')), [Point(0, 0), Point(1, 1)])
		self.assertEqual(list(a.find('X')), [])
		self.assertEqual(list(a.find_if(lambda c:c>'a')), [Point(1, 0), Point(0, 1)])
		self.assertEqual(list(a.find_if(lambda c:c<'a')), [])
	def should_transform_matrix(self):
		original = Matrix.fromstring('01\n23')
		processed = original.transform(int)
		self.assertEqual(processed.width, 2)
		self.assertEqual(processed.height, 2)
		self.assertEqual(processed.data, [
			0, 1,
			2, 3,
			])
	def should_construct_matrix_from_iterable(self):
		with self.assertRaises(ValueError):
			Matrix.from_iterable( (range(3), range(4)) )

		m = Matrix.from_iterable( (range(4), range(4, 8)) )
		self.assertEqual(m.width, 4)
		self.assertEqual(m.height, 2)
		self.assertEqual(m.data, [
			0, 1, 2, 3,
			4, 5, 6, 7,
			])
	def should_construct_matrix_from_multiline_string(self):
		data = textwrap.dedent("""\
				.X.X.
				XXXXX
				""")
		m = Matrix.fromstring(data)
		self.assertEqual(m.width, 5)
		self.assertEqual(m.height, 2)
		self.assertEqual(m.data, [
			'.', 'X', '.', 'X', '.',
			'X', 'X', 'X', 'X', 'X',
			])

		with self.assertRaises(ValueError):
			Matrix.fromstring("short\nlong")

		data = textwrap.dedent("""\
				.a.b.
				cabcd
				""")
		m = Matrix.fromstring(data, transformer=lambda c: -1 if c == '.' else ord(c) - ord('a'))
		self.assertEqual(m.width, 5)
		self.assertEqual(m.height, 2)
		self.assertEqual(m.data, [
			-1, 0, -1, 1, -1,
			2, 0, 1, 2, 3,
			])
	def should_convert_matrix_to_string(self):
		m = Matrix((5, 2))
		m.data = [
			'.', 'X', '.', 'X', '.',
			'X', 'X', 'X', 'X', 'X',
			]
		expected = textwrap.dedent("""\
				.X.X.
				XXXXX
				""")
		self.assertEqual(m.tostring(), expected)

		m = Matrix((5, 2))
		m.data = [
			-1, 0, -1, 1, -1,
			2, 0, 1, 2, 3,
			]
		expected = textwrap.dedent("""\
				.a.b.
				cabcd
				""")
		self.assertEqual(m.tostring(transformer=lambda c: '.' if c < 0 else chr(c + ord('a'))), expected)
	def should_fill_rectangle(self):
		m = Matrix((10, 5), '.')
		m.fill(Point(3, 1), Point(8, 3), 'X')
		expected = textwrap.dedent("""\
				..........
				...XXXXXX.
				...XXXXXX.
				...XXXXXX.
				..........
				""")
		actual = m.tostring()
		self.assertEqual(actual, expected)

class TestHexGrid(unittest.TestCase):
	def should_convert_hex_to_string_representation(self):
		grid = clckwrkbdgr.math.HexGrid(3, 5)
		grid.data.data = list(range(1, 1+15))
		grid.set_cell((1, 1), 'LONG')
		expected = textwrap.dedent(r"""
		 __    __    __ 
		/1 \__/3 \__/5 \
		\__/2 \__/4 \__/
		/6 \__/8 \__/10\
		\__/LO\__/9 \__/
		/11\__/13\__/15\
		\__/12\__/14\__/
		   \__/  \__/   
		"""[1:])
		self.assertEqual(grid.to_string(), expected)
	def should_get_hex_neighbours(self):
		grid = clckwrkbdgr.math.HexGrid(3, 5)
		grid.data.data = list(range(1, 1+15))
		neighbours = list(grid.get_neighbours(Point(1, 1)))
		self.assertEqual(neighbours, [
			Point(1, 0),
			Point(0, 1), Point(2, 1),
			Point(0, 2), Point(2, 2),
			Point(1, 2),
			])
		self.assertEqual([grid.get_cell(p) for p in neighbours], [2, 6, 8, 11, 13, 12])

class TestAlgorithms(unittest.TestCase):
	def should_get_neighbours(self):
		m = Matrix.fromstring('01\n23')
		neighbours = list(clckwrkbdgr.math.get_neighbours(m, (0, 0)))
		self.assertEqual(neighbours, [Point(1, 0), Point(0, 1)])
		neighbours = list(clckwrkbdgr.math.get_neighbours(m, (0, 0), with_diagonal=True))
		self.assertEqual(neighbours, [Point(1, 0), Point(0, 1), Point(1, 1)])

		neighbours = list(clckwrkbdgr.math.get_neighbours(m, (0, 0), check=lambda c: int(c) > 1))
		self.assertEqual(neighbours, [Point(0, 1)])
		neighbours = list(clckwrkbdgr.math.get_neighbours(m, (0, 0), with_diagonal=True, check=lambda c: int(c) > 1))
		self.assertEqual(neighbours, [Point(0, 1), Point(1, 1)])

class TestMath(unittest.TestCase):
	def should_extract_sign(self):
		self.assertEqual(clckwrkbdgr.math.sign(-100), -1)
		self.assertEqual(clckwrkbdgr.math.sign(-1), -1)
		self.assertEqual(clckwrkbdgr.math.sign(-0.5), -1)
		self.assertEqual(clckwrkbdgr.math.sign(0), 0)
		self.assertEqual(clckwrkbdgr.math.sign(+0.5), 1)
		self.assertEqual(clckwrkbdgr.math.sign(+1), +1)
		self.assertEqual(clckwrkbdgr.math.sign(+100), +1)
