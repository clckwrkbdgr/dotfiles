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
		appliance = appliances.ObjectAtPos(Point(1, 1), tree)
		self.assertEqual(str(appliance), 'tree @[1, 1]')

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
