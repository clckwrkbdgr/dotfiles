from .defs import *
from .engine import items
from .engine import actors
import clckwrkbdgr.math
from clckwrkbdgr.math import Direction

class Species(actors.Monster):
	""" Basic fixed stats shared by monsters of the same species.

	Vision - radius of field of vision (detection range).
	Drops - weighted distribution list of items: [(<weight>, <args...>), ...]
	Args can be None - to support probability that nothing is dropped.
	"""
	max_hp = NotImplemented
	vision = NotImplemented
	drops = None

class Monster(Species):
	""" Base for every living being (including player). """
	def __init__(self, pos):
		super(Monster, self).__init__(pos)
		self.hp = self.max_hp
		self.inventory = []
		self.wielding = None
	def __str__(self):
		return "{0} @{1} {2}/{3}hp".format(self.name, self.pos, self.hp, self.max_hp)
	@classmethod
	def load(cls, reader):
		species_name = reader.read()
		species = reader.get_meta_info('SPECIES')[species_name]
		pos = reader.read_point()
		monster = species(pos)
		monster.hp = reader.read_int()
		if reader.version > Version.INVENTORY:
			monster.inventory.extend(reader.read_list(items.Item))
		else:
			item_types = reader.get_meta_info('Items')
			from clckwrkbdgr.pcg import RNG
			monster.fill_inventory_from_drops(RNG(0), item_types)
		if reader.version > Version.WIELDING:
			monster.wielding = reader.read(items.Item, optional=True)
		return monster
	def save(self, writer):
		writer.write(type(self).__name__)
		writer.write(self.pos)
		writer.write(self.hp)
		writer.write(self.inventory)
		writer.write(self.wielding, optional=True)
	def is_alive(self):
		return self.hp > 0
	def _generate_drops(self, rng):
		from clckwrkbdgr import pcg
		if not self.drops:
			return []
		return [result for result
				in pcg.weighted_choices(rng, [(data[0], data[1:]) for data in self.drops])
				if result[0] is not None
				]
	def fill_inventory_from_drops(self, rng, item_types):
		for item_data in self._generate_drops(rng):
			item_type, item_data = item_data[0], item_data[1:]
			item = item_types[item_type](*item_data)
			self.inventory.append(item)
	def drop_loot(self):
		for item in self.inventory:
			item.pos = self.pos
		return self.inventory
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
