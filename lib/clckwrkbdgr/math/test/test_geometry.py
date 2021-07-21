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

		angle = geometry.GeoAngle.from_string(u"51°28′48″N")
		self.assertEqual(angle.degrees, 51)
		self.assertEqual(angle.minutes, 28)
		self.assertEqual(angle.seconds, 48)
		self.assertEqual(angle.direction, 'N')

		angle = geometry.GeoAngle.from_string(u"51o28'48\"n")
		self.assertEqual(angle.degrees, 51)
		self.assertEqual(angle.minutes, 28)
		self.assertEqual(angle.seconds, 48)
		self.assertEqual(angle.direction, 'N')

		angle = geometry.GeoAngle.from_string(u"0°0′0″E")
		self.assertEqual(angle.degrees, 0)
		self.assertEqual(angle.minutes, 0)
		self.assertEqual(angle.seconds, 0)
		self.assertEqual(angle.direction, 'E')
	def should_calculate_real_value_of_geo_angles(self):
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"51°28′48″N").get_value(), 51.48, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"0°0′0″E").get_value(), 0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"46°12′0″N").get_value(), 46.2, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"6°9′0″E").get_value(), 6.15, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"90°0′0″N").get_value(), 90.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"90°0′0″S").get_value(), -90.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"0°0′0″E").get_value(), 0.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"0°0′0″W").get_value(), 0.0, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"33°51′31″S").get_value(), -33.858, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"151°12′51″E").get_value(), 151.21, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"40°46′22″N").get_value(), 40.77, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"73°59′3″W").get_value(), -73.98, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"48°27′0″N").get_value(), 48.45, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"34°59′0″E").get_value(), 34.98, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"15°47′56″S").get_value(), -15.8, 2)
		self.assertAlmostEqual(geometry.GeoAngle.from_string(u"47°52′0″W").get_value(), -47.866, 2)
	def should_construct_geo_coord(self):
		latitude = geometry.GeoAngle.from_string(u"15°47′56″S")
		too_big_latitude = geometry.GeoAngle.from_string(u"115°47′56″S")
		longitude = geometry.GeoAngle.from_string(u"47°52′0″W")
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
		greenwich = geometry.GeoCoord.from_string(u"51°28′48″N", u"0°0′0″E")
		geneva = geometry.GeoCoord.from_string(u"46°12′0″N", u"6°9′0″E")
		self.assertAlmostEqual(greenwich.distance_to(geneva), 739.2, 1)
		self.assertAlmostEqual(geometry.GeoCoord.from_string(u"90°0′0″N 0°0′0″E").distance_to(
			geometry.GeoCoord.from_string(u"90°0′0″S, 0°0′0″W")
			), 20015.1, 1) # From South to North
		self.assertAlmostEqual(geometry.GeoCoord.from_string(u"33°51′31″S, 151°12′51″E").distance_to(
			geometry.GeoCoord.from_string(u"40°46′22″N 73°59′3″W")
			), 15990.2, 1) # Opera Night
		self.assertAlmostEqual(geometry.GeoCoord.from_string(u"48°27′0″N,34°59′0″E").distance_to(
			geometry.GeoCoord.from_string(u"15°47′56″S 47°52′0″W")
			), 10801.62, 1)
