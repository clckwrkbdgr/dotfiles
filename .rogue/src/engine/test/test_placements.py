from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import appliances
from ..mock import *

VERSION = 666

class TestAppliances(unittest.TestCase):
	def should_str_appliance(self):
		tree = Tree()
		self.assertEqual(str(tree), 'tree')
		self.assertEqual(repr(tree), 'Tree(tree)')
	def should_str_appliance_at_pos(self):
		tree = Tree()
		appliance = appliances.ObjectAtPos(Point(1, 1), None)
		appliance.obj = tree
		self.assertEqual(str(appliance), 'tree @[1, 1]')
		self.assertEqual(appliance, appliance)
		self.assertEqual(appliance, tree)

class TestAppliancesSavefile(unittest.TestCase):
	def should_load_appliance(self):
		stream = StringIO(str(VERSION) + '\x00Tree')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'Tree':Tree})
		appliance = reader.read(appliances.Appliance)
		self.assertEqual(type(appliance), Tree)
	def should_save_appliance(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		appliance = Tree()
		writer.write(appliance)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Tree')
	def should_load_appliance_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00Statue\x00goddess')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'Statue':Statue})
		appliance = reader.read(appliances.Appliance)
		self.assertEqual(type(appliance), Statue)
		self.assertEqual(appliance.likeness, 'goddess')
	def should_save_appliance_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		appliance = Statue('goddess')
		writer.write(appliance)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Statue\x00goddess')

class TestDoors(unittest.TestCase):
	def should_load_level_passage(self):
		stream = StringIO(str(VERSION) + '\x00Door\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'Door':Door})
		door = reader.read(appliances.Appliance)
		self.assertEqual(type(door), Door)
		self.assertTrue(door.is_closed())
	def should_save_level_passage(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		door = Door(False)
		writer.write(door)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Door\x000')
	def should_open_and_close_door(self):
		door = Door(True)
		self.assertTrue(door.is_closed())
		door.open()
		self.assertFalse(door.is_closed())
		door.close()
		self.assertTrue(door.is_closed())

		door.toggle()
		self.assertFalse(door.is_closed())
		door.toggle()
		self.assertTrue(door.is_closed())
	def should_make_door_impassable_when_closed(self):
		door = Door(True)
		self.assertFalse(door.passable)
		door.open()
		self.assertTrue(door.passable)
		door.close()
		self.assertFalse(door.passable)
	def should_switch_sprites_when_door_is_closed(self):
		door = Door(True)
		self.assertEqual(door.sprite, Door._closed_sprite)
		door.open()
		self.assertEqual(door.sprite, Door._opened_sprite)
		door.close()
		self.assertEqual(door.sprite, Door._closed_sprite)

class TestLevelPassages(unittest.TestCase):
	def should_load_level_passage(self):
		stream = StringIO(str(VERSION) + '\x00StairsDown\x00next_level\x00enter')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'StairsDown':StairsDown})
		stairs = reader.read(appliances.Appliance)
		self.assertEqual(type(stairs), StairsDown)
		self.assertEqual(stairs.level_id, 'next_level')
		self.assertEqual(stairs.connected_passage, 'enter')
	def should_save_level_passage(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		stairs = StairsDown('next_level', 'enter')
		writer.write(stairs)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00StairsDown\x00next_level\x00enter')
	def should_travel_via_level_passage(self):
		stairs = StairsDown('next_level', 'enter')
		rogue = Rogue(None)
		self.assertEqual(stairs.use(rogue), ('next_level', 'enter'))
	def should_travel_via_locked_level_passage(self):
		stairs = StairsUp('surface', 'entrance')
		rogue = Rogue(None)

		with self.assertRaises(StairsUp.Locked) as e:
			stairs.use(rogue)
		self.assertEqual(str(e.exception), 'Locked; required Gold to unlock')

		rogue.grab(Gold())
		self.assertEqual(stairs.use(rogue), ('surface', 'entrance'))

class TestApplianceAtPosSavefile(unittest.TestCase):
	def should_load_appliance_at_pos(self):
		stream = StringIO(str(VERSION) + '\x00Statue\x00goddess\x001\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'Statue':Statue})
		pos, appliance = reader.read(appliances.ObjectAtPos)
		self.assertEqual(type(appliance), Statue)
		self.assertEqual(appliance.likeness, 'goddess')
		self.assertEqual(pos, Point(1, 1))
	def should_save_appliance_at_pos(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		appliance = Statue('goddess')
		appliance = appliances.ObjectAtPos(Point(1, 1), appliance)
		writer.write(appliance)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Statue\x00goddess\x001\x001')
