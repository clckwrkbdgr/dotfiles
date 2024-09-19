import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from ..math import Point
from .. import monsters
from .. import items
from ..pcg import RNG
from ..system import savefile
from ..defs import Version
from . import mock_dungeon

class TestSpecies(unittest.TestCase):
	def should_str_species(self):
		self.assertEqual(str(monsters.Species('name', '@', 100, vision=10)), 'name 100hp')

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		species = monsters.Species('name', '@', 100, vision=10)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(str(monster), 'name @1;1 100/100hp')
	def should_not_drop_items(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=None)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster._generate_drops(rng), [])
	def should_drop_items(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=[
			(1, 'potion'),
			(2, 'money'),
			(3, 'rags'),
			])
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster._generate_drops(rng), [('potion',)])
		self.assertEqual(monster._generate_drops(rng), [('rags',)])
		self.assertEqual(monster._generate_drops(rng), [('money',)])
		self.assertEqual(monster._generate_drops(rng), [('rags',)])

		monster.fill_inventory_from_drops(rng, mock_dungeon.MockGame0.ITEMS)
		drops = monster.drop_loot()
		self.assertEqual(len(drops), 1)
		self.assertEqual(drops[0].item_type.name, 'potion')
	def should_drop_nothing_sometimes(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=[
			(1, None),
			(2, 'money'),
			(3, None),
			])
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster._generate_drops(rng), [])
		self.assertEqual(monster._generate_drops(rng), [])
		self.assertEqual(monster._generate_drops(rng), [('money',)])
		self.assertEqual(monster._generate_drops(rng), [])
		self.assertEqual(monster._generate_drops(rng), [])

class TestSavefile(unittest.TestCase):
	def should_load_monster(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x003\x001\x001\x003\x001\x00money\x001\x001\x001\x00weapon\x000\x000')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', mock_dungeon.MockGame0.SPECIES)
		reader.set_meta_info('ITEMS', mock_dungeon.MockGame0.ITEMS)
		monster = reader.read(monsters.Monster)
		self.assertEqual(monster.species, mock_dungeon.MockGame0.SPECIES['name'])
		self.assertEqual(monster.behavior, monsters.Behavior.ANGRY)
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 1)
		self.assertEqual(monster.inventory[0].item_type.name, 'money')
		self.assertEqual(monster.inventory[0].pos, monster.pos)
		self.assertEqual(monster.wielding.item_type.name, 'weapon')
		self.assertEqual(monster.wielding.pos, Point(0, 0))
	def should_load_monster_without_inventory(self):
		stream = StringIO(str(Version.INVENTORY) + '\x00name\x003\x001\x001\x003')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', mock_dungeon.MockGame0.SPECIES)
		reader.set_meta_info('ITEMS', mock_dungeon.MockGame0.ITEMS)
		monster = reader.read(monsters.Monster)
		self.assertEqual(monster.species, mock_dungeon.MockGame0.SPECIES['name'])
		self.assertEqual(monster.behavior, monsters.Behavior.ANGRY)
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 1)
		self.assertEqual(monster.inventory[0].item_type.name, 'money')
		self.assertEqual(monster.inventory[0].pos, monster.pos)
	def should_load_monster_without_wielding_equipment(self):
		stream = StringIO(str(Version.WIELDING) + '\x00name\x003\x001\x001\x003\x000')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', mock_dungeon.MockGame0.SPECIES)
		reader.set_meta_info('ITEMS', mock_dungeon.MockGame0.ITEMS)
		monster = reader.read(monsters.Monster)
		self.assertEqual(monster.species, mock_dungeon.MockGame0.SPECIES['name'])
		self.assertEqual(monster.behavior, monsters.Behavior.ANGRY)
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 0)
		self.assertIsNone(monster.wielding)

	def should_save_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		monster = monsters.Monster(mock_dungeon.MockGame0.SPECIES['name'], monsters.Behavior.ANGRY, Point(1, 1))
		monster.wielding = items.Item(mock_dungeon.MockGame0.ITEMS['weapon'], Point(0, 0))
		monster.fill_inventory_from_drops(RNG(0), mock_dungeon.MockGame0.ITEMS)
		monster.hp = 3
		writer.write(monster)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00name\x003\x001\x001\x003\x001\x00money\x001\x001\x001\x00weapon\x000\x000')
