import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from ..math import Point
from .. import monsters
from ..pcg import RNG
from ..system import savefile
from ..game import Version # TODO global defs module

class TestSpecies(unittest.TestCase):
	def should_str_species(self):
		self.assertEqual(str(monsters.Species('name', '@', 100, vision=10)), 'name 100hp')

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		species = monsters.Species('name', '@', 100, vision=10)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(str(monster), 'name @Point(x=1, y=1) 100/100hp')
	def should_not_drop_items(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=None)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster.drop_loot(rng), [])
	def should_drop_items(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=[
			(1, 'potion'),
			(2, 'money'),
			(3, 'rags'),
			])
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster.drop_loot(rng), [('potion',)])
		self.assertEqual(monster.drop_loot(rng), [('rags',)])
		self.assertEqual(monster.drop_loot(rng), [('money',)])
		self.assertEqual(monster.drop_loot(rng), [('rags',)])
		self.assertEqual(monster.drop_loot(rng), [('potion',)])
	def should_drop_nothing_sometimes(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=[
			(1, None),
			(2, 'money'),
			(3, None),
			])
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster.drop_loot(rng), [])
		self.assertEqual(monster.drop_loot(rng), [])
		self.assertEqual(monster.drop_loot(rng), [('money',)])
		self.assertEqual(monster.drop_loot(rng), [])
		self.assertEqual(monster.drop_loot(rng), [])

class TestSavefile(unittest.TestCase):
	def setUp(self):
		self.SPECIES = {
				'name' : monsters.Species('name', 'M', 100, vision=10),
				'player' : monsters.Species('name', '@', 100, vision=10),
				}
	def should_load_monster(self):
		stream = StringIO('666\x00name\x003\x001\x001\x003')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', self.SPECIES)
		reader.set_meta_info('Version.MONSTER_BEHAVIOR', Version.MONSTER_BEHAVIOR) # TODO global defs module should be created and used everywhere instead.
		monster = reader.read(monsters.Monster)
		self.assertEqual(monster.species, self.SPECIES['name'])
		self.assertEqual(monster.behavior, monsters.Behavior.ANGRY)
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
	def should_save_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, 666)
		monster = monsters.Monster(self.SPECIES['name'], monsters.Behavior.ANGRY, Point(1, 1))
		monster.hp = 3
		writer.write(monster)
		self.assertEqual(stream.getvalue(), '666\x00name\x003\x001\x001\x003')
