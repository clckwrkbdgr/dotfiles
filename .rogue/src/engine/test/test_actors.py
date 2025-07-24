from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import actors, items
from ..mock import *
from clckwrkbdgr import pcg

VERSION = 666

class TestActors(unittest.TestCase):
	def should_str_actor(self):
		dragonfly = Dragonfly(Point(1, 1))
		self.assertEqual(str(dragonfly), 'dragonfly')
		self.assertEqual(repr(dragonfly), 'Dragonfly(dragonfly @[1, 1])')
	def should_load_actor(self):
		stream = StringIO(str(VERSION) + '\x00Dragonfly\x001\x002')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'Dragonfly':Dragonfly})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), Dragonfly)
		self.assertEqual(actor.pos, Point(1, 2))
	def should_save_actor(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = Dragonfly(Point(1, 2))
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Dragonfly\x001\x002')
	def should_load_actor_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00Butterfly\x001\x002\x00red')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'Butterfly':Butterfly})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), Butterfly)
		self.assertEqual(actor.pos, Point(1, 2))
		self.assertEqual(actor.color, 'red')
	def should_save_actor_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = Butterfly(Point(1, 2), color='red')
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Butterfly\x001\x002\x00red')

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		rat = Rat(Point(1, 1))
		self.assertEqual(str(rat), 'rat')
		self.assertEqual(repr(rat), 'Rat(rat @[1, 1] 10/10hp)')
	def should_load_monster(self):
		stream = StringIO(str(VERSION) + '\x00Rat\x001\x002\x0010\x001\x00Potion')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Actors', {'Rat':Rat})
		reader.set_meta_info('Items', {'Potion':Potion})
		actor = reader.read(actors.Actor)
		self.assertEqual(type(actor), Rat)
		self.assertEqual(actor.pos, Point(1, 2))
		self.assertEqual(list(map(repr, actor.inventory)), ['Potion(potion)'])
	def should_save_monster(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		actor = Rat(Point(1, 2))
		actor.grab(Potion())
		writer.write(actor)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Rat\x001\x002\x0010\x001\x00Potion')
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
	def should_calculate_attack_damage(self):
		rat = Rat(Point(1, 1))
		self.assertEqual(rat.get_attack_damage(), 1)
	def should_calculate_protection(self):
		rat = Rat(Point(1, 1))
		self.assertEqual(rat.get_protection(), 0)
		rat = PackRat(Point(1, 1))
		self.assertEqual(rat.get_protection(), 1)
	def should_hurt_monster(self):
		rat = Rat(Point(1, 1))
		self.assertEqual(rat.affect_health(-5), -5)
		self.assertEqual(rat.hp, 5)
		self.assertEqual(rat.affect_health(-10), -5)
		self.assertEqual(rat.hp, 0)
	def should_detect_hostiles(self):
		rogue = Rogue(None)
		rat = Rat(None)
		goblin = Goblin(None)
		pack_rat = PackRat(None)

		self.assertTrue(rogue.is_hostile_to(rat))
		self.assertTrue(rogue.is_hostile_to(goblin))
		self.assertTrue(rogue.is_hostile_to(pack_rat))

		self.assertTrue(rat.is_hostile_to(rogue))
		self.assertFalse(rat.is_hostile_to(goblin))
		self.assertFalse(rat.is_hostile_to(pack_rat))

		self.assertTrue(pack_rat.is_hostile_to(rogue))
		self.assertFalse(pack_rat.is_hostile_to(rat))
		self.assertFalse(pack_rat.is_hostile_to(goblin))

		self.assertTrue(goblin.is_hostile_to(rogue))
		self.assertFalse(goblin.is_hostile_to(rat))
		self.assertTrue(goblin.is_hostile_to(pack_rat))
	def should_resolve_item(self):
		rat = PackRat(Point(1, 1))
		potion = Potion()
		rat.grab(potion)
		mcguffin = Gold()
		rat.grab(mcguffin)
		self.assertEqual(rat._resolve_item(potion), potion)
		self.assertEqual(len(rat.inventory), 2)
		self.assertEqual(rat._resolve_item(1), mcguffin)
		self.assertEqual(len(rat.inventory), 2)
		self.assertEqual(rat._resolve_item(1, remove=True), mcguffin)
		self.assertEqual(len(rat.inventory), 1)
		self.assertEqual(rat._resolve_item(potion, remove=True), potion)
		self.assertEqual(len(rat.inventory), 0)
	def should_find_items_in_inventory(self):
		rat = PackRat(Point(1, 1))
		potion = Potion()
		self.assertEqual(list(rat.iter_items(Potion)), [])
		self.assertIsNone(rat.find_item(Potion))
		rat.grab(potion)
		self.assertEqual(list(rat.iter_items(Potion)), [potion])
		self.assertEqual(rat.find_item(Potion), potion)
		self.assertEqual(list(rat.iter_items(Rags)), [])

		note_x = ScribbledNote('X')
		rat.grab(note_x)
		self.assertEqual(list(rat.iter_items(ScribbledNote)), [note_x])
		self.assertEqual(list(rat.iter_items(ScribbledNote, text='X')), [note_x])
		self.assertEqual(list(rat.iter_items(ScribbledNote, text='not X')), [])

		note_not_x = ScribbledNote('X')
		rat.grab(note_not_x)
		self.assertEqual(list(rat.iter_items(ScribbledNote)), [note_x, note_not_x])
	def should_detect_items_in_inventory(self):
		rat = PackRat(Point(1, 1))
		potion = Potion()
		self.assertFalse(rat.has_item(Potion))
		rat.grab(potion)
		self.assertTrue(rat.has_item(Potion))
		self.assertFalse(rat.has_item(Rags))
		note = ScribbledNote('X')
		rat.grab(note)
		self.assertTrue(rat.has_item(ScribbledNote))
		self.assertTrue(rat.has_item(ScribbledNote, text='X'))
		self.assertFalse(rat.has_item(ScribbledNote, text='not X'))
	def should_not_overflow_inventory(self):
		rat = Rat(Point(1, 1))
		potion = Potion()
		rat.grab(potion)

		note = ScribbledNote('X')
		with self.assertRaises(actors.Monster.InventoryFull):
			rat.grab(note)
	def should_drop_item(self):
		rat = Rat(Point(1, 1))
		potion = Potion()
		rat.grab(potion)
		self.assertEqual(rat.drop(potion), items.ItemAtPos(Point(1, 1), potion))
		self.assertFalse(rat.inventory)
	def should_drop_item_by_key(self):
		rat = Rat(Point(1, 1))
		potion = Potion()
		rat.grab(potion)
		self.assertEqual(rat.drop(0), items.ItemAtPos(Point(1, 1), potion))
		self.assertFalse(rat.inventory)
	def should_drop_all_item(self):
		rat = PackRat(Point(1, 1))
		potion_1 = Potion()
		potion_2 = Potion()
		mcguffin = Gold()
		rat.grab(potion_1)
		rat.grab(mcguffin)
		rat.grab(potion_2)
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
			Potion(),
			])))
		self.assertEqual(rat.drops, [])
	def should_fill_random_drops_with_multiple_items(self):
		rat = PackRat(Point(1, 1))
		rat.fill_drops(pcg.RNG(0))
		self.assertEqual(list(map(repr, rat.inventory)), list(map(repr, [
			Gold(),
			])))
		self.assertEqual(rat.drops, [])
	def should_consume_item(self):
		rat = Rat(Point(1, 1))
		rat.hp = 6
		potion = Potion()
		rat.grab(potion)
		self.assertEqual(repr(rat.consume(potion)), repr([Healed(rat, +4)]))
		self.assertEqual(rat.hp, 10)
		self.assertFalse(rat.inventory)

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
		goblin.grab(dagger)
		goblin.grab(rags)
		goblin.wield(dagger)
		self.assertEqual(goblin.wielding, dagger)
		self.assertFalse(goblin.has_item(Dagger))
		with self.assertRaises(Goblin.SlotIsTaken):
			goblin.wield(rags)
		self.assertEqual(goblin.wielding, dagger)
	def should_unwield_items(self):
		goblin = Goblin(Point(1, 2))
		dagger = Dagger()
		goblin.grab(dagger)
		self.assertIsNone(goblin.unwield())
		goblin.wield(dagger)
		self.assertEqual(goblin.wielding, dagger)
		self.assertEqual(goblin.unwield(), dagger)
		self.assertIsNone(goblin.wielding)
		self.assertTrue(goblin.has_item(Dagger))
	def should_wear_items(self):
		goblin = Goblin(Point(1, 2))
		dagger = Dagger()
		rags = Rags()
		rags_2 = Rags()
		goblin.grab(dagger)
		goblin.grab(rags)
		goblin.grab(rags_2)
		with self.assertRaises(Goblin.ItemNotFit):
			goblin.wear(dagger)
		self.assertIsNone(goblin.wearing)
		goblin.wear(rags)
		self.assertEqual(goblin.wearing, rags)
		self.assertEqual(len(list(goblin.iter_items(Rags))), 1)
		with self.assertRaises(Goblin.SlotIsTaken):
			goblin.wear(rags_2)
		self.assertEqual(goblin.wearing, rags)
	def should_take_off_items(self):
		goblin = Goblin(Point(1, 2))
		rags = Rags()
		goblin.grab(rags)
		self.assertIsNone(goblin.take_off())
		goblin.wear(rags)
		self.assertEqual(goblin.wearing, rags)
		self.assertEqual(goblin.take_off(), rags)
		self.assertIsNone(goblin.wearing)
		self.assertTrue(goblin.has_item(Rags))
	def should_calculate_attack_damage(self):
		goblin = Goblin(Point(1, 1))
		self.assertEqual(goblin.get_attack_damage(), 1)
		dagger = Dagger()
		rags = Rags()
		goblin.grab(rags)
		goblin.grab(dagger)
		goblin.wield(dagger)
		self.assertEqual(goblin.get_attack_damage(), 2)
		goblin.unwield()
		goblin.wield(rags)
		self.assertEqual(goblin.get_attack_damage(), 1)
	def should_calculate_protection(self):
		goblin = Goblin(Point(1, 1))
		self.assertEqual(goblin.get_protection(), 0)
		rags = Rags()
		goblin.grab(rags)
		goblin.wear(rags)
		self.assertEqual(goblin.get_protection(), 1)
