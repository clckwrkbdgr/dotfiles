from .defs import *
from clckwrkbdgr.collections import DocstringEnum as Enum
from . import items
from .engine import actors

class Behavior(Enum):
	""" PLAYER
	DUMMY
	INERT
	ANGRY
	"""

class Species(actors.Monster):
	""" Basic fixed stats shared by monsters of the same species.

	Vision - radius of field of vision (detection range).
	Drops - weighted distribution list of items: [(<weight>, <args...>), ...]
	Args can be None - to support probability that nothing is dropped.
	"""
	name = NotImplemented
	sprite = NotImplemented
	max_hp = NotImplemented
	vision = NotImplemented
	drops = None

class Monster(Species):
	""" Base for every living being (including player). """
	def __init__(self, behavior, pos):
		super(Monster, self).__init__(pos)
		self.species = self
		self.behavior = behavior
		self.hp = self.species.max_hp
		self.inventory = []
		self.wielding = None
	def __str__(self):
		return "{0} @{1} {2}/{3}hp".format(self.species.name, self.pos, self.hp, self.species.max_hp)
	@classmethod
	def load(cls, reader):
		species_name = reader.read()
		species = reader.get_meta_info('SPECIES')[species_name]
		if reader.version > Version.MONSTER_BEHAVIOR:
			behavior = reader.read_int()
		else:
			if species_name == 'player':
				behavior = Behavior.PLAYER
			else:
				behavior = Behavior.DUMMY
		pos = reader.read_point()
		monster = species(behavior, pos)
		monster.hp = reader.read_int()
		if reader.version > Version.INVENTORY:
			monster.inventory.extend(reader.read_list(items.Item))
		else:
			item_types = reader.get_meta_info('ITEMS')
			from clckwrkbdgr.pcg import RNG
			monster.fill_inventory_from_drops(RNG(0), item_types)
		if reader.version > Version.WIELDING:
			monster.wielding = reader.read(items.Item, optional=True)
		return monster
	def save(self, writer):
		writer.write(type(self).__name__)
		writer.write(self.behavior)
		writer.write(self.pos)
		writer.write(self.hp)
		writer.write(self.inventory)
		writer.write(self.wielding, optional=True)
	def is_alive(self):
		return self.hp > 0
	def _generate_drops(self, rng):
		from clckwrkbdgr import pcg
		if not self.species.drops:
			return []
		return [result for result
				in pcg.weighted_choices(rng, [(data[0], data[1:]) for data in self.species.drops])
				if result[0] is not None
				]
	def fill_inventory_from_drops(self, rng, item_types):
		for item_data in self._generate_drops(rng):
			item_type, item_data = item_data[0], item_data[1:]
			item_data = (item_types[item_type],) + item_data
			item = items.Item(*item_data)
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
