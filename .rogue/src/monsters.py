from .utils import Enum

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
	def __str__(self):
		return "{0} @{1} {2}/{3}hp".format(self.species.name, self.pos, self.hp, self.species.max_hp)
	@classmethod
	def load(cls, reader):
		species_name = reader.read()
		species = reader.get_meta_info('SPECIES')[species_name]
		if reader.version > reader.get_meta_info('Version.MONSTER_BEHAVIOR'):
			behavior = reader.read_int()
		else:
			if species_name == 'player':
				behavior = Behavior.PLAYER
			else:
				behavior = Behavior.ANGRY
		pos = reader.read_point()
		monster = cls(species, behavior, pos)
		monster.hp = reader.read_int()
		return monster
	def save(self, writer):
		writer.write(self.species.name)
		writer.write(self.behavior)
		writer.write(self.pos)
		writer.write(self.hp)
	def is_alive(self):
		return self.hp > 0
	@property
	def name(self):
		return self.species.name
	def drop_loot(self, rng):
		from . import pcg
		if not self.species.drops:
			return []
		return [result for result
				in pcg.weighted_choices(rng, [(data[0], data[1:]) for data in self.species.drops])
				if result[0] is not None
				]
	def __eq__(self, other):
		if not isinstance(other, Monster):
			return False
		return self.species == other.species \
				and self.pos == other.pos \
				and self.hp == other.hp
