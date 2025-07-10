from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import actors, items

VERSION = 666

class MockPotion(items.Item):
	_sprite = '!'
	_name = 'potion'

class MockActor(actors.Actor):
	_sprite = '@'
	_name = 'rogue'

class MockMonster(actors.Monster):
	_max_hp = 10

class ColoredMonster(actors.Monster):
	def __init__(self, *args, **kwargs):
		self.color = kwargs.get('color')
		if 'color' in kwargs:
			del kwargs['color']
		super(ColoredMonster, self).__init__(*args, **kwargs)
	def load(self, stream):
		super(ColoredMonster, self).load(stream)
		self.color = stream.read()
	def save(self, stream):
		super(ColoredMonster, self).save(stream)
		stream.write(self.color)

class TestActors(unittest.TestCase):
	def should_str_actor(self):
		rogue = MockActor(Point(1, 1))
		self.assertEqual(str(rogue), 'rogue')
		self.assertEqual(repr(rogue), 'MockActor(rogue @[1, 1])')

class TestActorsSavefile(unittest.TestCase):
	def should_load_actor(self):
		stream = StringIO(str(VERSION) + '\x00MockActor\x001\x002')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'MockActor':MockActor})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), MockActor)
		self.assertEqual(actor.pos, Point(1, 2))
	def should_save_actor(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = MockActor(Point(1, 2))
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00MockActor\x001\x002')
	def should_load_monster(self):
		stream = StringIO(str(VERSION) + '\x00MockMonster\x001\x002\x0010\x001\x00MockPotion')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'MockMonster':MockMonster})
		reader.set_meta_info('Items', {'MockPotion':MockPotion})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), MockMonster)
		self.assertEqual(actor.pos, Point(1, 2))
		self.assertEqual(list(map(repr, actor.inventory)), ['MockPotion(potion)'])
	def should_save_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = MockMonster(Point(1, 2))
		actor.inventory.append(MockPotion())
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00MockMonster\x001\x002\x0010\x001\x00MockPotion')
	def should_load_actor_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00ColoredMonster\x001\x002\x001\x000\x00red')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'ColoredMonster':ColoredMonster})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), ColoredMonster)
		self.assertEqual(actor.pos, Point(1, 2))
		self.assertEqual(actor.color, 'red')
	def should_save_actor_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = ColoredMonster(Point(1, 2), color='red')
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ColoredMonster\x001\x002\x001\x000\x00red')
