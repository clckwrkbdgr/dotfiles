import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point
from .. import monsters
from ..engine import items
from clckwrkbdgr.pcg import RNG
import clckwrkbdgr.serialize.stream as savefile
from ..defs import Version
from . import mock_dungeon

class MockSpecies(monsters.Monster):
	name = 'name'
	sprite = '@'
	max_hp = 100
	vision = 10
	drops = None

class MockSpeciesWithDrops(MockSpecies):
	drops = [
			(1, 'potion'),
			(2, 'money'),
			(3, 'rags'),
			]

class MockSpeciesWithPoorDrops(MockSpecies):
	drops = [
			(1, None),
			(2, 'money'),
			(3, None),
			]

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		monster = MockSpecies(Point(1, 1))
		self.assertEqual(str(monster), 'name @[1, 1] 100/100hp')
	def should_not_drop_items(self):
		rng = RNG(0)
		monster = MockSpecies(Point(1, 1))
		self.assertEqual(monster._generate_drops(rng), [])
	def should_drop_items(self):
		rng = RNG(0)
		monster = MockSpeciesWithDrops(Point(1, 1))
		self.assertEqual(monster._generate_drops(rng), [('potion',)])
		self.assertEqual(monster._generate_drops(rng), [('rags',)])
		self.assertEqual(monster._generate_drops(rng), [('money',)])
		self.assertEqual(monster._generate_drops(rng), [('rags',)])

		monster.fill_inventory_from_drops(rng, mock_dungeon.MockGame.ITEMS)
		drops = monster.drop_loot()
		self.assertEqual(len(drops), 1)
		self.assertEqual(drops[0].name, 'potion')
	def should_drop_nothing_sometimes(self):
		rng = RNG(0)
		monster = MockSpeciesWithPoorDrops(Point(1, 1))
		self.assertEqual(monster._generate_drops(rng), [])
		self.assertEqual(monster._generate_drops(rng), [])
		self.assertEqual(monster._generate_drops(rng), [('money',)])
		self.assertEqual(monster._generate_drops(rng), [])
		self.assertEqual(monster._generate_drops(rng), [])

class TestSavefile(unittest.TestCase):
	def should_load_monster(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x001\x001\x003\x001\x00money\x001\x00weapon')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', mock_dungeon.MockGame.SPECIES)
		reader.set_meta_info('Items', mock_dungeon.MockGame.ITEMS)
		monster = reader.read(monsters.Monster)
		self.assertEqual(type(monster), mock_dungeon.MockGame.SPECIES['name'])
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 1)
		self.assertEqual(monster.inventory[0].name, 'money')
		self.assertEqual(monster.wielding.name, 'weapon')
	def should_load_monster_without_inventory(self):
		stream = StringIO(str(Version.INVENTORY) + '\x00name\x001\x001\x003')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', mock_dungeon.MockGame.SPECIES)
		reader.set_meta_info('Items', mock_dungeon.MockGame.ITEMS)
		monster = reader.read(monsters.Monster)
		self.assertEqual(type(monster), mock_dungeon.MockGame.SPECIES['name'])
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 1)
		self.assertEqual(monster.inventory[0].name, 'money')
	def should_load_monster_without_wielding_equipment(self):
		stream = StringIO(str(Version.WIELDING) + '\x00name\x001\x001\x003\x000')
		reader = savefile.Reader(stream)
		reader.set_meta_info('SPECIES', mock_dungeon.MockGame.SPECIES)
		reader.set_meta_info('Items', mock_dungeon.MockGame.ITEMS)
		monster = reader.read(monsters.Monster)
		self.assertEqual(type(monster), mock_dungeon.MockGame.SPECIES['name'])
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 0)
		self.assertIsNone(monster.wielding)

	def should_save_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		monster = mock_dungeon.MockGame.SPECIES['name'](Point(1, 1))
		monster.wielding = mock_dungeon.MockGame.ITEMS['weapon']()
		monster.fill_inventory_from_drops(RNG(0), mock_dungeon.MockGame.ITEMS)
		monster.hp = 3
		writer.write(monster)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00Name\x001\x001\x003\x001\x00Money\x001\x00Weapon')
