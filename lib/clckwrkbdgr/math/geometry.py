# -*- coding: utf-8 -*-
import re, math
try:
	math.gcd
except AttributeError: # pragma: no cover -- py2
	import fractions
	math.gcd = fractions.gcd
import clckwrkbdgr.math
import clckwrkbdgr.utils

class Line(object):
	""" 2D segment between two points on plane. """
	def __init__(self, a, b):
		self.a = clckwrkbdgr.math.Point(a)
		self.b = clckwrkbdgr.math.Point(b)
	def __str__(self): # pragma: no cover
		return '{0}~{1}'.format(self.a, self.b)
	def __repr__(self): # pragma: no cover
		return 'Line({0}, {1})'.format(repr(self.a), repr(self.b))
	def connected_to(self, other):
		""" Checks if two segments have common point.
		Returns that point or None otherwise.
		"""
		other = [other.a, other.b]
		if self.a in other:
			return self.a
		if self.b in other:
			return self.b
		return None
	def length(self):
		""" Returns total length of the segment. """
		return math.hypot(self.a.x - self.b.x, self.a.y - self.b.y)
	def direction(self):
		""" Returns 2D Vector for the line that contains this segment.
		First component is always positive.
		"""
		d_x = self.b.x - self.a.x
		d_y = self.b.y - self.a.y
		gcd = math.gcd(abs(d_x), abs(d_y))
		if gcd > 1:
				d_x //= gcd
				d_y //= gcd
		if d_x < 0:
				d_x = -d_x
				d_y = -d_y
		return clckwrkbdgr.math.Vector(d_x, d_y)
	def line_equation(self):
		""" Returns coefficients of line equation for the line that contains this segment:
		A x + B y + C = 0
		"""
		x1, y1 = self.a
		x2, y2 = self.b
		a = (y2 - y1)
		b = (x1 - x2)
		c = (x2 - x1) * y1 - x1 * (y2 - y1)
		return a, b, c

def triangle_area(A, B, C):
	""" Calculates area of triangle given by Points. """
	segments = Line(A, B), Line(B, C), Line(C, A)
	a, b, c = map(Line.length, segments)
	s = (a + b + c) / 2.
	return math.sqrt(s * (s - a) * (s - b) * (s - c))

class GeoAngle(object):
	def __init__(self, degrees, minutes, seconds, direction):
		""" Constructs geographical coordinate (angle on sphere).
		Degress, minutes, seconds should be positive integer numbers within corresponding range.
		Direction should be one of 'N', 'E', 'W', 'S'
		"""
		self._validate(degrees, 180, "Degrees")
		self.degrees = degrees
		self._validate(minutes, 60, "Minutes")
		self.minutes = minutes
		self._validate(seconds, 60, "Seconds")
		self.seconds = seconds
		if direction.upper() not in ['N', 'E', 'W', 'S']:
			raise ValueError("Direction should be one of NEWS: {0}".format(repr(direction)))
		self.direction = direction.upper()
	def _validate(self, number, top_bound, name):
		if not clckwrkbdgr.utils.is_integer(number):
			raise ValueError("{1} should be integer: {0}".format(number, name))
		if number < 0 or top_bound <= number:
			raise ValueError("{1} should be in range [0; {2}): {0}".format(number, name, top_bound))
	def get_value(self):
		""" Returns real degree value as a signed float. """
		signs = {'N':1,'S':-1,'E':1,'W':-1}
		return signs[self.direction] * (float(self.degrees) + float(self.minutes) / 60.0 + float(self.seconds) / 3600.0)
	@classmethod
	def from_string(cls, value):
		""" Constructs geographical angle from strings like: 0\u00b00\u20320\u2033N, 0o0'0"E
		Both Unicode and ASCII symbols may be used.
		"""
		pattern = re.compile(u'^(\\d+)(?:\u00b0|[Oo])(\\d+)(?:\u2032|\')(\\d+)(?:\u2033|")([NEWSnews])$')
		m = pattern.match(value)
		if not m:
			raise ValueError("Value does not match pattern XXoXX'XX\"[NEWS]: {0}".format(repr(value)))
		degrees, minutes, seconds, direction = m.groups()
		return cls(int(degrees), int(minutes), int(seconds), direction)

def haversine(phi1, lambda1, phi2, lambda2, radius):
	""" Calculates distance between two points on sphere of given radius.
	Points are specified by their angles:
	- phi: vertical position (latitude);
	- lambda: horizontal position (longitude).
	"""
	phi1, lambda1, phi2, lambda2 = map(math.radians, (phi1, lambda1, phi2, lambda2))
	d_phi = phi2 - phi1
	d_lambda = lambda2 - lambda1
	a = math.sin(d_phi/2.) * math.sin(d_phi/2.) + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2.) * math.sin(d_lambda/2.)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
	d = radius * c
	return d

class GeoCoord(object):
	""" Geographic coordinates. """
	def __init__(self, latitude, longitude):
		""" Constructs coord pair from latitude and longitude.
		Elevation is not considered.
		"""
		if 90 < abs(latitude.get_value()):
			raise ValueError("Invalid value for latitude: too big: {0}".format(latitude.get_value()))
		if latitude.direction not in ['N', 'S']:
			raise ValueError("Invalid direction for latitude {0}, accepting only N or S.".format(latitude.direction))
		self.latitude = latitude
		if longitude.direction not in ['E', 'W']:
			raise ValueError("Invalid direction for longitude {0}, accepting only E or W.".format(longitude.direction))
		self.longitude = longitude
	def distance_to(self, other, radius=6371.0):
		return haversine(
				self.latitude.get_value(),
				self.longitude.get_value(),
				other.latitude.get_value(),
				other.longitude.get_value(),
				radius
				)
	@classmethod
	def from_string(cls, latitude_str, longitude_str=None):
		""" Constructs geographical coords from string(s).
		If only one value is given, it is considered to contain
		both lat and lon separated by comma and/or space.
		"""
		if longitude_str is None:
			latitude_str, longitude_str = re.split(r'[ ,]+', latitude_str)
		return cls(
				GeoAngle.from_string(latitude_str),
				GeoAngle.from_string(longitude_str),
				)
