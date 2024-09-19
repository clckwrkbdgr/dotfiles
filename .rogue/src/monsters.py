from .defs import *
from .utils import Enum
from . import items

class Behavior(Enum):
	""" PLAYER
	DUMMY
	INERT
	ANGRY
	"""

class Species(object):
	""" Basic fixed stats shared by monsters of the same species. """
	def __init__(self, name, sprite, max_hp, vision, drops=None):
		""" Vision - radius of field of vision (detection range).
		Drops - weighted distribution list of items: [(<weight>, <args...>), ...]
		Args can be None - to support probability that nothing is dropped.
		"""
		self.name = name
		self.sprite = sprite
		self.max_hp = max_hp
		self.vision = vision
		self.drops = drops
	def __str__(self):
		return "{0} {1}hp".format(self.name, self.max_hp)

class Monster(object):
	""" Base for every living being (including player). """
	def __init__(self, species, behavior, pos):
		self.species = species
		self.behavior = behavior
		self.pos = pos
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
				behavior = Behavior.ANGRY
		pos = reader.read_point()
		monster = cls(species, behavior, pos)
		monster.hp = reader.read_int()
		if reader.version > Version.INVENTORY:
			monster.inventory.extend(reader.read_list(items.Item))
		else:
			item_types = reader.get_meta_info('ITEMS')
			from .pcg import RNG
			monster.fill_inventory_from_drops(RNG(0), item_types)
		if reader.version > Version.WIELDING:
			monster.wielding = reader.read(items.Item, optional=True)
		return monster
	def save(self, writer):
		writer.write(self.species.name)
		writer.write(self.behavior)
		writer.write(self.pos)
		writer.write(self.hp)
		writer.write(self.inventory)
		writer.write(self.wielding, optional=True)
	def is_alive(self):
		return self.hp > 0
	@property
	def name(self):
		return self.species.name
	def _generate_drops(self, rng):
		from . import pcg
		if not self.species.drops:
			return []
		return [result for result
				in pcg.weighted_choices(rng, [(data[0], data[1:]) for data in self.species.drops])
				if result[0] is not None
				]
	def fill_inventory_from_drops(self, rng, item_types):
		for item_data in self._generate_drops(rng):
			item_type, item_data = item_data[0], item_data[1:]
			item_data = (item_types[item_type],) + item_data + (self.pos,)
			item = items.Item(*item_data)
			self.inventory.append(item)
	def drop_loot(self):
		for item in self.inventory:
			item.pos = self.pos
		return self.inventory
	def __eq__(self, other):
		if not isinstance(other, Monster):
			return False
		return self.species == other.species \
				and self.pos == other.pos \
				and self.hp == other.hp
