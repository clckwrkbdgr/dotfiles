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
from ..engine import actors

class TestSavefile(unittest.TestCase):
	def should_load_monster(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x001\x001\x003\x001\x00money\x001\x00weapon')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', mock_dungeon.MockGame.SPECIES)
		reader.set_meta_info('Items', mock_dungeon.MockGame.ITEMS)
		monster = reader.read(actors.Actor)
		self.assertEqual(type(monster), mock_dungeon.MockGame.SPECIES['name'])
		self.assertEqual(monster.pos, Point(1, 1))
		self.assertEqual(monster.hp, 3)
		self.assertEqual(len(monster.inventory), 1)
		self.assertEqual(monster.inventory[0].name, 'money')
		self.assertEqual(monster.wielding.name, 'weapon')
	def should_load_monster_without_wielding_equipment(self):
		stream = StringIO(str(Version.WIELDING) + '\x00name\x001\x001\x003\x000')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', mock_dungeon.MockGame.SPECIES)
		reader.set_meta_info('Items', mock_dungeon.MockGame.ITEMS)
		monster = reader.read(actors.Actor)
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
		monster.fill_drops(RNG(0))
		monster.hp = 3
		writer.write(monster)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00Name\x001\x001\x003\x001\x00Money\x001\x00Weapon')
