import logging
Log = logging.getLogger(__name__)
from ..math import Point, Rect, Size
"""
Binary space partition generators.
"""

class BinarySpacePartition(object):
	""" Builder object to generate sequence of rooms in binary space partition.
	See generate().
	"""
	def __init__(self, rng, min_width=15, min_height=10):
		self.rng = rng
		self.min_size = (min_width, min_height)
		self._unfit_both_dimensions = False
	def set_unfit_both_dimensions(self, value):
		""" Commands build to discard new split if resulting rooms unfit
		in any direction, e.g. either too narrow or too low.
		By default is False, i.e. discards only rooms unfit in both directions
		at the same time, but still can produce gallery-like long rooms.
		"""
		self._unfit_both_dimensions = bool(value)
	def door_generator(self, room): # pragma: no cover
		""" Takes a Rect object and generates random Point for door position inside it.
		No need to determine wall facing and location, the algorithm would decide automatically.
		By default door is generated in random manner.
		"""
		x = self.rng.range(room.topleft.x, room.topleft.x + room.size.width - 1)
		y = self.rng.range(room.topleft.y, room.topleft.y + room.size.height - 1)
		Log.debug("Generating door in {0}:  ({1}, {2})".format(room, x, y))
		return Point(x, y)
	def hor_ver_generator(self): # pragma: no cover
		""" Used to determine direction of the split for the current room.
		It should return True for horizontal and False for vertical room.
		By default these values are generated in random manner.
		"""
		return self.rng.choice([False, True])
	def generate(self, topleft, bottomright):
		""" Generates BS partition for given rectangle.
		Yield tuples (topleft, bottomright, is_horizontal, door).
		Tuples go from the biggest room to the all subrooms descending.
		Sibling rooms go left-to-right and top-to-bottom.
		"""
		Log.debug("topleft={0}, bottomright={1}".format(topleft, bottomright))
		too_narrow = abs(topleft.x - bottomright.x) <= self.min_size[0]
		too_low = abs(topleft.y - bottomright.y) <= self.min_size[1]
		unfit = False
		if self._unfit_both_dimensions:
			unfit = too_narrow or too_low
		else:
			unfit = too_narrow and too_low
		if unfit:
			return
		horizontal = False if too_narrow else (True if too_low else self.hor_ver_generator())
		new_topleft = Point(topleft.x + 2, topleft.y + 2)
		userspace = Rect(
				new_topleft,
				Size(
					bottomright.x - new_topleft.x + 1,
					bottomright.y - new_topleft.y + 1,
				))
		if userspace.size.width <= 0 or userspace.size.height <= 0:
			return
		assert userspace.size.width > 1 or userspace.size.height > 1
		if self._unfit_both_dimensions:
			for _ in range(userspace.size.width * userspace.size.height):
				door = self.door_generator(userspace)
				if horizontal:
					left_bound = userspace.topleft.x + self.min_size[0]
					right_bound = userspace.topleft.x + userspace.size.width - self.min_size[0]
					if not (left_bound <= door.x <= right_bound):
						continue
				else:
					top_bound = userspace.topleft.y + self.min_size[1]
					bottom_bound = userspace.topleft.y + userspace.size.height - self.min_size[1]
					if not (top_bound <= door.y <= bottom_bound):
						continue
				break
			else:
				return
		else:
			door = self.door_generator(userspace)
		assert userspace.contains(door, with_border=True), "Door {0} not in room user space {1}".format(door, userspace)
		yield (topleft, bottomright, horizontal, door)
		if horizontal:
			the_divide, door_pos = door
			for x in self.generate(topleft, Point(the_divide - 1, bottomright.y)):
				yield x
			for x in self.generate(Point(the_divide + 1, topleft.y), bottomright):
				yield x
		else:
			door_pos, the_divide = door
			for x in self.generate(topleft, Point(bottomright.x, the_divide - 1)):
				yield x
			for x in self.generate(Point(topleft.x, the_divide + 1), bottomright):
				yield x

