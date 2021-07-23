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

class RectConnection(object):
	""" Rectangular connection between two points on discrete plane.
	Lines follow main axes with single bridge at some bending point to
	connect beginning/ending lines.
	Form depends on direction (horizontal, vertical).
	     ####>   V
	 Hor #       #  Ver
	     #       #
	>#####       ######
	                  #
	                  #
	                  V
	"""
	def __init__(self, start, stop, direction, bending_point):
		""" Start and stop point will be sorted internally for convenience purposes
		(from left to right for H, from top to bottom for V).
		Direction must be a single char: H or V.
		Bending point is a distance from the start to the bridge.
		It must be relative to the leftmost (topmost) point
		depending on the direction. It must be in range of (0; stop-start)
		"""
		if direction not in ['H', 'V']:
			raise ValueError("Invalid direction {0}, must be one of: 'H', 'V'".format(repr(direction)))
		self.direction = direction
		start, stop = map(clckwrkbdgr.math.Point, (start, stop))
		self.start, self.stop = sorted(
				[start, stop],
				key=(lambda p: p.x) if self.direction == 'H' else (lambda p: p.y)
				)
		bending_point_range = (
				abs(self.start.x - self.stop.x)
				if self.direction == 'H'
				else abs(self.start.y - self.stop.y)
				)
		if not (0 < bending_point < bending_point_range):
			raise ValueError("Bending point should be in range (0; {0}): {1}".format(bending_point_range, bending_point))
		self.bending_point = bending_point
	def __setstate__(self, data): # pragma: no cover -- TODO
		self.start = data['start']
		self.stop = data['stop']
		self.direction = data['direction']
		self.bending_point = data['bending']
	def __getstate__(self): # pragma: no cover -- TODO
		return {
				'start': self.start,
				'stop': self.stop,
				'direction': self.direction,
				'bending': self.bending_point,
				}
	def contains(self, pos):
		""" Returns True if point lies on connection lines (beginning segment, ending segment or the bridge).
		For non-integer points behavior is undefined.
		"""
		pos = clckwrkbdgr.math.Point(pos)
		if self.direction == 'H':
			if pos.x < self.start.x + self.bending_point:
				return pos.x >= self.start.x and pos.y == self.start.y
			elif pos.x > self.start.x + self.bending_point:
				return pos.x <= self.stop.x and pos.y == self.stop.y
			else:
				return min(self.start.y, self.stop.y) <= pos.y <= max(self.start.y, self.stop.y)
		else:
			if pos.y < self.start.y + self.bending_point:
				return pos.y >= self.start.y and pos.x == self.start.x
			elif pos.y > self.start.y + self.bending_point:
				return pos.y <= self.stop.y and pos.x == self.stop.x
			else:
				return min(self.start.x, self.stop.x) <= pos.x <= max(self.start.x, self.stop.x)
	def iter_points(self):
		""" Iterates over integer points on connection lines (beginning segment -> the bridge -> ending segment).
		"""
		if self.direction == 'H':
			lead = self.start.y
			for x in range(self.start.x, self.stop.x + 1):
				yield clckwrkbdgr.math.Point(x, lead)
				if x == self.start.x + self.bending_point:
					if self.start.y < self.stop.y:
						for y in range(self.start.y + 1, self.stop.y + 1):
							yield clckwrkbdgr.math.Point(x, y)
					else:
						for y in reversed(range(self.stop.y, self.start.y)):
							yield clckwrkbdgr.math.Point(x, y)
					lead = self.stop.y
		else:
			lead = self.start.x
			for y in range(self.start.y, self.stop.y + 1):
				yield clckwrkbdgr.math.Point(lead, y)
				if y == self.start.y + self.bending_point:
					if self.start.x < self.stop.x:
						for x in range(self.start.x + 1, self.stop.x + 1):
							yield clckwrkbdgr.math.Point(x, y)
					else:
						for x in reversed(range(self.stop.x, self.start.x)):
							yield clckwrkbdgr.math.Point(x, y)
					lead = self.stop.x
