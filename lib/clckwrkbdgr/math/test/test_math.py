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
		self.assertEqual(hash(rect), hash((rect.topleft, rect.size)))
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

class TestMath(unittest.TestCase):
	def should_extract_sign(self):
		self.assertEqual(clckwrkbdgr.math.sign(-100), -1)
		self.assertEqual(clckwrkbdgr.math.sign(-1), -1)
		self.assertEqual(clckwrkbdgr.math.sign(-0.5), -1)
		self.assertEqual(clckwrkbdgr.math.sign(0), 0)
		self.assertEqual(clckwrkbdgr.math.sign(+0.5), 1)
		self.assertEqual(clckwrkbdgr.math.sign(+1), +1)
		self.assertEqual(clckwrkbdgr.math.sign(+100), +1)
