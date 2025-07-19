from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import appliances

VERSION = 666

class MockStairs(appliances.Appliance):
	_sprite = '>'
	_name = 'stairs'

class ColoredDoor(appliances.Appliance):
	_sprite = '+'
	_name = 'door'
	def __init__(self, color='transparent'):
		self.color = color
	def load(self, stream):
		self.color = stream.read()
	def save(self, stream):
		super(ColoredDoor, self).save(stream)
		stream.write(self.color)

class TestAppliances(unittest.TestCase):
	def should_str_appliance(self):
		stairs = MockStairs()
		self.assertEqual(str(stairs), 'stairs')
		self.assertEqual(repr(stairs), 'MockStairs(stairs)')
	def should_str_appliance_at_pos(self):
		stairs = MockStairs()
		appliance = appliances.ObjectAtPos(Point(1, 1), stairs)
		self.assertEqual(str(appliance), 'stairs @[1, 1]')

class TestAppliancesSavefile(unittest.TestCase):
	def should_load_appliance(self):
		stream = StringIO(str(VERSION) + '\x00MockStairs')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'MockStairs':MockStairs})
		appliance = reader.read(appliances.Appliance)
		self.assertEqual(type(appliance), MockStairs)
	def should_save_appliance(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		appliance = MockStairs()
		writer.write(appliance)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00MockStairs')
	def should_load_appliance_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00ColoredDoor\x00red')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'ColoredDoor':ColoredDoor})
		appliance = reader.read(appliances.Appliance)
		self.assertEqual(type(appliance), ColoredDoor)
		self.assertEqual(appliance.color, 'red')
	def should_save_appliance_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		appliance = ColoredDoor('red')
		writer.write(appliance)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ColoredDoor\x00red')

class TestApplianceAtPosSavefile(unittest.TestCase):
	def should_load_appliance_at_pos(self):
		stream = StringIO(str(VERSION) + '\x00ColoredDoor\x00red\x001\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Appliances', {'ColoredDoor':ColoredDoor})
		pos, appliance = reader.read(appliances.ObjectAtPos)
		self.assertEqual(type(appliance), ColoredDoor)
		self.assertEqual(appliance.color, 'red')
		self.assertEqual(pos, Point(1, 1))
	def should_save_appliance_at_pos(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		appliance = ColoredDoor('red')
		appliance = appliances.ObjectAtPos(Point(1, 1), appliance)
		writer.write(appliance)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ColoredDoor\x00red\x001\x001')
