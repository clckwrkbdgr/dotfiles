# -*- coding: utf-8 -*-
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import clckwrkbdgr.math
from clckwrkbdgr.math import geometry
from clckwrkbdgr.math import Point

class TestLine(unittest.TestCase):
	def should_detect_if_two_segments_are_connected(self):
		first = geometry.Line((1, 2), (3, 4))
		second = geometry.Line((5, 6), (3, 4))
		third = geometry.Line((5, 6), (4, 3))
		self.assertEqual(first.connected_to(second), Point(3, 4))
		self.assertEqual(second.connected_to(first), Point(3, 4))
		self.assertEqual(second.connected_to(third), Point(5, 6))
		self.assertIsNone(first.connected_to(third))
	def should_calculation_direction_vector_for_segment(self):
		line = geometry.Line((1, 2), (3, 4))
		self.assertEqual(line.direction(), clckwrkbdgr.math.Vector(1, 1))
		line = geometry.Line((1, 2), (1, 4))
		self.assertEqual(line.direction(), clckwrkbdgr.math.Vector(0, 1))
		line = geometry.Line((5, 5), (6, 4))
		self.assertEqual(line.direction(), clckwrkbdgr.math.Vector(1, -1))
		line = geometry.Line((6, 4), (5, 5))
		self.assertEqual(line.direction(), clckwrkbdgr.math.Vector(1, -1))
	def should_calculation_equation_coeffs(self):
		self.assertEqual(geometry.Line((11, 2), (8, 3)).line_equation(), (1, 3, -17))
		self.assertEqual(geometry.Line((2, 2), (5, 7)).line_equation(), (5, -3, -4))

class TestGeometry(unittest.TestCase):
	def should_calculate_area_of_triangle(self):
		self.assertAlmostEqual(geometry.triangle_area( (0, 0), (0, 1), (1, 0) ), 0.5)
		self.assertAlmostEqual(geometry.triangle_area( (1, 2), (3, 4), (6, 5) ), 2.0)
		self.assertAlmostEqual(geometry.triangle_area( (1, 2), (3, 4), (5, 6) ), 0)

class TestGeoCoords(unittest.TestCase):
	def should_construct_spherical_angles(self):
		angle = geometry.GeoAngle(51, 28, 48, 'N')
		self.assertEqual(angle.degrees, 51)
		self.assertEqual(angle.minutes, 28)
		self.assertEqual(angle.seconds, 48)
		self.assertEqual(angle.direction, 'N')

		self.assertRaises(ValueError, geometry.GeoAngle, 51.1, 28, 48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, -51, 28, 48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 351, 28, 48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 28.1, 48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, -28, 48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 128, 48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 28, 48.1, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 28, -48, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 28, 148, 'N')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 28, 48, 'NORTH')
		self.assertRaises(ValueError, geometry.GeoAngle, 51, 28, 48, 'not a direction')
	def should_parse_spherical_angles_from_string(self):
		with self.assertRaises(ValueError):
			geometry.GeoAngle.from_string(u"51 28 48 N")
		with self.assertRaises(ValueError):
			geometry.GeoAngle.from_string("not an angle at all")

		angle = geometry.GeoAngle.from_string(u"51\u00b028\u203248\u2033N")
		self.assertEqual(angle.degrees, 51)
		self.assertEqual(angle.minutes, 28)
		self.assertEqual(angle.seconds, 48)
		self.assertEqual(angle.direction, 'N')

		angle = geometry.GeoAngle.from_string(u"51o28'48\"n")
		self.assertEqual(angle.degrees, 51)
		self.assertEqual(angle.minutes, 28)
		self.assertEqual(angle.seconds, 48)
		self.assertEqual(angle.direction, 'N')

		angle = geometry.GeoAngle.from_string(u"0\u00b00\u20320\u2033E")
		self.assertEqual(angle.degrees, 0)
		self.assertEqual(angle.minutes, 0)
		self.assertEqual(angle.seconds, 0)
		self.assertEqual(angle.direction, 'E')
	def should_calculate_real_value_of_geo_angles(self):
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"51\u00b028\u203248\u2033N").get_value(), 51.48, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"0\u00b00\u20320\u2033E").get_value(), 0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"46\u00b012\u20320\u2033N").get_value(), 46.2, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"6\u00b09\u20320\u2033E").get_value(), 6.15, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"90\u00b00\u20320\u2033N").get_value(), 90.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"90\u00b00\u20320\u2033S").get_value(), -90.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"0\u00b00\u20320\u2033E").get_value(), 0.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"0\u00b00\u20320\u2033W").get_value(), 0.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"33\u00b051\u203231\u2033S").get_value(), -33.858, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"151\u00b012\u203251\u2033E").get_value(), 151.21, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"40\u00b046\u203222\u2033N").get_value(), 40.77, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"73\u00b059\u20323\u2033W").get_value(), -73.98, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"48\u00b027\u20320\u2033N").get_value(), 48.45, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"34\u00b059\u20320\u2033E").get_value(), 34.98, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"15\u00b047\u203256\u2033S").get_value(), -15.8, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"47\u00b052\u20320\u2033W").get_value(), -47.866, 2)
	def should_construct_geo_coord(self):
		latitude = geometry.GeoAngle.from_string(u"15\u00b047\u203256\u2033S")
		too_big_latitude = geometry.GeoAngle.from_string(u"115\u00b047\u203256\u2033S")
		longitude = geometry.GeoAngle.from_string(u"47\u00b052\u20320\u2033W")
		with self.assertRaises(ValueError):
			geometry.GeoCoord(longitude, longitude)
		with self.assertRaises(ValueError):
			geometry.GeoCoord(latitude, latitude)
		with self.assertRaises(ValueError):
			geometry.GeoCoord(too_big_latitude, longitude)

		coord = geometry.GeoCoord(latitude, longitude)
		self.assertEqual(coord.latitude, latitude)
		self.assertEqual(coord.longitude, longitude)
	def should_calculate_distances_between_geo_coords(self):
		greenwich = geometry.GeoCoord.from_string(u"51\u00b028\u203248\u2033N", u"0\u00b00\u20320\u2033E")
		geneva = geometry.GeoCoord.from_string(u"46\u00b012\u20320\u2033N", u"6\u00b09\u20320\u2033E")
		self.assertAlmostEqual(greenwich.distance_to(geneva), 739.2, 1)
		self.assertAlmostEqual(geometry.GeoCoord.from_string(u"90\u00b00\u20320\u2033N 0\u00b00\u20320\u2033E").distance_to(
			geometry.GeoCoord.from_string(u"90\u00b00\u20320\u2033S, 0\u00b00\u20320\u2033W")
			), 20015.1, 1) # From South to North
		self.assertAlmostEqual(geometry.GeoCoord.from_string(u"33\u00b051\u203231\u2033S, 151\u00b012\u203251\u2033E").distance_to(
			geometry.GeoCoord.from_string(u"40\u00b046\u203222\u2033N 73\u00b059\u20323\u2033W")
			), 15990.2, 1) # Opera Night
		self.assertAlmostEqual(geometry.GeoCoord.from_string(u"48\u00b027\u20320\u2033N,34\u00b059\u20320\u2033E").distance_to(
			geometry.GeoCoord.from_string(u"15\u00b047\u203256\u2033S 47\u00b052\u20320\u2033W")
			), 10801.62, 1)

class TestRectConnection(unittest.TestCase):
	def should_create_and_validate_connection(self):
		with self.assertRaises(ValueError):
			geometry.RectConnection((0, 0), (5, 5), 'not a direction', 2)
		with self.assertRaises(ValueError):
			geometry.RectConnection((0, 0), (5, 5), 'H', 100500)
		conn = geometry.RectConnection((5, 5), (0, 0), 'H', 2)
		self.assertEqual(conn.start, Point(0, 0))
		self.assertEqual(conn.stop, Point(5, 5))
		self.assertEqual(conn.direction, 'H')
		self.assertEqual(conn.bending_point, 2)
	def should_iterate_over_points(self):
		self.maxDiff = None
		conn = geometry.RectConnection((5, 5), (0, 0), 'V', 2)
		self.assertEqual(list(conn.iter_points()), [
			Point(0, 0),
			Point(0, 1),
			Point(0, 2), Point(1, 2), Point(2, 2), Point(3, 2), Point(4, 2), Point(5, 2),
			Point(5, 3),
			Point(5, 4),
			Point(5, 5),
			])
		conn = geometry.RectConnection((5, 0), (0, 5), 'V', 2)
		self.assertEqual(list(conn.iter_points()), [
			Point(5, 0),
			Point(5, 1),
			Point(5, 2), Point(4, 2), Point(3, 2), Point(2, 2), Point(1, 2), Point(0, 2),
			Point(0, 3),
			Point(0, 4),
			Point(0, 5),
			])
		conn = geometry.RectConnection((5, 5), (0, 0), 'H', 3)
		self.assertEqual(list(conn.iter_points()), [
			Point(0, 0),
			Point(1, 0),
			Point(2, 0),
			Point(3, 0), Point(3, 1), Point(3, 2), Point(3, 3), Point(3, 4), Point(3, 5),
			Point(4, 5),
			Point(5, 5),
			])
		conn = geometry.RectConnection((0, 5), (5, 0), 'H', 3)
		self.assertEqual(list(conn.iter_points()), [
			Point(0, 5),
			Point(1, 5),
			Point(2, 5),
			Point(3, 5), Point(3, 4), Point(3, 3), Point(3, 2), Point(3, 1), Point(3, 0),
			Point(4, 0),
			Point(5, 0),
			])
	def should_detect_points_on_connection_lines(self):
		conn = geometry.RectConnection((5, 5), (0, 0), 'V', 2)
		self.assertTrue(conn.contains((0, 0)))
		self.assertTrue(conn.contains((0, 2)))
		self.assertTrue(conn.contains((2, 2)))
		self.assertTrue(conn.contains((5, 2)))
		self.assertTrue(conn.contains((5, 5)))
		self.assertFalse(conn.contains((0, 5)))
		self.assertFalse(conn.contains((2, 3)))
		conn = geometry.RectConnection((5, 5), (0, 0), 'H', 3)
		self.assertTrue(conn.contains((0, 0)))
		self.assertFalse(conn.contains((0, 2)))
		self.assertTrue(conn.contains((2, 0)))
		self.assertFalse(conn.contains((2, 2)))
		self.assertTrue(conn.contains((3, 3)))
		self.assertTrue(conn.contains((5, 5)))
		self.assertFalse(conn.contains((0, 5)))
		self.assertFalse(conn.contains((2, 3)))
