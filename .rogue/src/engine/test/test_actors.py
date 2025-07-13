from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import actors, items
from clckwrkbdgr import pcg

VERSION = 666

class MockPotion(items.Item):
	_sprite = '!'
	_name = 'potion'

class Dagger(items.Item):
	_sprite = '('
	_name = 'dagger'

class Rags(items.Item, items.Wearable):
	_sprite = '['
	_name = 'rags'

class McGuffin(items.Item):
	_sprite = '*'
	_name = 'mcguffin'

class MockActor(actors.Actor):
	_sprite = '@'
	_name = 'rogue'

class Rat(actors.Monster):
	_sprite = 'r'
	_name = 'rat'
	_max_hp = 10
	_drops = [
			(1, None),
			(5, MockPotion),
			]

class PackRat(Rat):
	_drops = [
			[
				(6, None),
				(1, MockPotion),
				],
			[
				(1, McGuffin),
				],
			]

class Goblin(actors.EquippedMonster):
	_sprite = 'g'
	_name = 'goblin'
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

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		rat = Rat(Point(1, 1))
		self.assertEqual(str(rat), 'rat')
		self.assertEqual(repr(rat), 'Rat(rat @[1, 1] 10/10hp)')
	def should_load_monster(self):
		stream = StringIO(str(VERSION) + '\x00Rat\x001\x002\x0010\x001\x00MockPotion')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'Rat':Rat})
		reader.set_meta_info('Items', {'MockPotion':MockPotion})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), Rat)
		self.assertEqual(actor.pos, Point(1, 2))
		self.assertEqual(list(map(repr, actor.inventory)), ['MockPotion(potion)'])
	def should_save_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = Rat(Point(1, 2))
		actor.inventory.append(MockPotion())
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Rat\x001\x002\x0010\x001\x00MockPotion')
	def should_detect_alive_monster(self):
		rat = Rat(Point(1, 1))
		self.assertTrue(rat.is_alive())
		rat.hp = 0
		self.assertFalse(rat.is_alive())
	def should_heal_monster(self):
		rat = Rat(Point(1, 1))
		rat.hp = 5
		self.assertEqual(rat.affect_health(1), 1)
		self.assertEqual(rat.hp, 6)
		self.assertEqual(rat.affect_health(10), 4)
		self.assertEqual(rat.hp, 10)
	def should_hurt_monster(self):
		rat = Rat(Point(1, 1))
		self.assertEqual(rat.affect_health(-5), -5)
		self.assertEqual(rat.hp, 5)
		self.assertEqual(rat.affect_health(-10), -5)
		self.assertEqual(rat.hp, 0)
	def should_resolve_item(self):
		rat = Rat(Point(1, 1))
		potion = MockPotion()
		rat.inventory.append(potion)
		mcguffin = McGuffin()
		rat.inventory.append(mcguffin)
		self.assertEqual(rat._resolve_item(potion), potion)
		self.assertEqual(len(rat.inventory), 2)
		self.assertEqual(rat._resolve_item(1), mcguffin)
		self.assertEqual(len(rat.inventory), 2)
		self.assertEqual(rat._resolve_item(1, remove=True), mcguffin)
		self.assertEqual(len(rat.inventory), 1)
		self.assertEqual(rat._resolve_item(potion, remove=True), potion)
		self.assertEqual(len(rat.inventory), 0)
	def should_drop_item(self):
		rat = Rat(Point(1, 1))
		potion = MockPotion()
		rat.inventory.append(potion)
		self.assertEqual(rat.drop(potion), items.ItemAtPos(Point(1, 1), potion))
		self.assertFalse(rat.inventory)
	def should_drop_item_by_key(self):
		rat = Rat(Point(1, 1))
		potion = MockPotion()
		rat.inventory.append(potion)
		self.assertEqual(rat.drop(0), items.ItemAtPos(Point(1, 1), potion))
		self.assertFalse(rat.inventory)
	def should_drop_all_item(self):
		rat = Rat(Point(1, 1))
		potion_1 = MockPotion()
		potion_2 = MockPotion()
		mcguffin = McGuffin()
		rat.inventory.append(potion_1)
		rat.inventory.append(mcguffin)
		rat.inventory.append(potion_2)
		self.assertEqual(list(rat.drop_all()), [
			items.ItemAtPos(Point(1, 1), potion_2),
			items.ItemAtPos(Point(1, 1), mcguffin),
			items.ItemAtPos(Point(1, 1), potion_1),
			])
		self.assertFalse(rat.inventory)
	def should_fill_random_drops(self):
		rat = Rat(Point(1, 1))
		rat.fill_drops(pcg.RNG(1))
		self.assertEqual(list(map(repr, rat.inventory)), list(map(repr, [
			MockPotion(),
			])))
		self.assertEqual(rat.drops, [])
	def should_fill_random_drops_with_multiple_items(self):
		rat = PackRat(Point(1, 1))
		rat.fill_drops(pcg.RNG(0))
		self.assertEqual(list(map(repr, rat.inventory)), list(map(repr, [
			McGuffin(),
			])))
		self.assertEqual(rat.drops, [])

class TestEquippedMonsters(unittest.TestCase):
	def should_load_equpped_monster(self):
		stream = StringIO(str(VERSION) + '\x00Goblin\x001\x002\x0010\x000\x001\x00Dagger\x001\x00Rags')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'Goblin':Goblin})
		reader.set_meta_info('Items', {'Dagger':Dagger,'Rags':Rags})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), Goblin)
		self.assertEqual(actor.pos, Point(1, 2))
		self.assertEqual(repr(actor.wielding), repr(Dagger()))
		self.assertEqual(repr(actor.wearing), repr(Rags()))
	def should_save_equpped_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		goblin = Goblin(Point(1, 2))
		goblin.wielding = Dagger()
		goblin.wearing = Rags()
		writer.write(goblin)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Goblin\x001\x002\x0010\x000\x001\x00Dagger\x001\x00Rags')
	
	def should_wield_items(self):
		goblin = Goblin(Point(1, 2))
		dagger = Dagger()
		rags = Rags()
		goblin.inventory.append(dagger)
		goblin.inventory.append(rags)
		goblin.wield(dagger)
		self.assertEqual(goblin.wielding, dagger)
		self.assertFalse(dagger in goblin.inventory)
		with self.assertRaises(Goblin.SlotIsTaken):
			goblin.wield(rags)
		self.assertEqual(goblin.wielding, dagger)
	def should_unwield_items(self):
		goblin = Goblin(Point(1, 2))
		dagger = Dagger()
		goblin.inventory.append(dagger)
		self.assertIsNone(goblin.unwield())
		goblin.wield(dagger)
		self.assertEqual(goblin.wielding, dagger)
		self.assertEqual(goblin.unwield(), dagger)
		self.assertIsNone(goblin.wielding)
		self.assertTrue(dagger in goblin.inventory)
	def should_wear_items(self):
		goblin = Goblin(Point(1, 2))
		dagger = Dagger()
		rags = Rags()
		rags_2 = Rags()
		goblin.inventory.append(dagger)
		goblin.inventory.append(rags)
		goblin.inventory.append(rags_2)
		with self.assertRaises(Goblin.ItemNotFit):
			goblin.wear(dagger)
		self.assertIsNone(goblin.wearing)
		goblin.wear(rags)
		self.assertEqual(goblin.wearing, rags)
		self.assertFalse(rags in goblin.inventory)
		with self.assertRaises(Goblin.SlotIsTaken):
			goblin.wear(rags_2)
		self.assertEqual(goblin.wearing, rags)
	def should_take_off_items(self):
		goblin = Goblin(Point(1, 2))
		rags = Rags()
		goblin.inventory.append(rags)
		self.assertIsNone(goblin.take_off())
		goblin.wear(rags)
		self.assertEqual(goblin.wearing, rags)
		self.assertEqual(goblin.take_off(), rags)
		self.assertIsNone(goblin.wearing)
		self.assertTrue(rags in goblin.inventory)
