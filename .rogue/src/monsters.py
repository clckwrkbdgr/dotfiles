from .defs import *
from .engine import items
from .engine import actors
import clckwrkbdgr.math
from clckwrkbdgr.math import Direction

class Monster(actors.Monster):
	""" Base for every living being (including player).

	Vision - radius of field of vision (detection range).
	Drops - weighted distribution list of items: [(<weight>, <args...>), ...]
	Args can be None - to support probability that nothing is dropped.
	"""
	vision = NotImplemented
	def __init__(self, pos):
		super(Monster, self).__init__(pos)
		self.wielding = None
	def load(self, reader):
		super(Monster, self).load(reader)
		monster = self
		if reader.version > Version.WIELDING:
			monster.wielding = reader.read(items.Item, optional=True)
		return monster
	def save(self, writer):
		super(Monster, self).save(writer)
		writer.write(self.wielding, optional=True)
	def __eq__(self, other):
		if not isinstance(other, Monster):
			return False
		return type(self) == type(other) \
				and self.pos == other.pos \
				and self.hp == other.hp
	def perform_action(self, game):
		pass

class Angry(Monster):
	def perform_action(self, game):
		player = game.get_player()
		if not player: # pragma: no cover
			return
		if clckwrkbdgr.math.distance(self.pos, player.pos) == 1:
			game.attack(self, player)
		elif clckwrkbdgr.math.distance(self.pos, player.pos) <= self.vision:
			is_transparent = lambda p: game.is_transparent_to_monster(p, self)
			if clckwrkbdgr.math.algorithm.FieldOfView.in_line_of_sight(self.pos, player.pos, is_transparent):
				direction = Direction.from_points(self.pos, player.pos)
				game.move(self, direction)

class Inert(Monster):
	def perform_action(self, game):
		player = game.get_player()
		if not player: # pragma: no cover
			return
		if clckwrkbdgr.math.distance(self.pos, player.pos) == 1:
			game.attack(self, player)
