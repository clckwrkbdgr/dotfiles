from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import items
from ..mock import *

VERSION = 666

class TestItems(unittest.TestCase):
	def should_str_item(self):
		potion = Potion()
		self.assertEqual(str(potion), 'potion')
		self.assertEqual(repr(potion), 'Potion(potion)')
	def should_str_item_at_pos(self):
		potion = Potion()
		item = items.ItemAtPos(Point(1, 1), potion)
		self.assertEqual(str(item), 'potion @[1, 1]')

class TestItemsSavefile(unittest.TestCase):
	def should_load_item(self):
		stream = StringIO(str(VERSION) + '\x00Potion')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Items', {'Potion':Potion})
		item = reader.read(items.Item)
		self.assertEqual(type(item), Potion)
	def should_save_item(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		item = Potion()
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00Potion')
	def should_load_item_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00ScribbledNote\x00beware of dog')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Items', {'ScribbledNote':ScribbledNote})
		item = reader.read(items.Item)
		self.assertEqual(type(item), ScribbledNote)
		self.assertEqual(item.text, 'beware of dog')
	def should_save_item_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		item = ScribbledNote('beware of dog')
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ScribbledNote\x00beware of dog')

class TestItemAtPosSavefile(unittest.TestCase):
	def should_load_item_at_pos(self):
		stream = StringIO(str(VERSION) + '\x00ScribbledNote\x00beware of dog\x001\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Items', {'ScribbledNote':ScribbledNote})
		pos, item = reader.read(items.ItemAtPos)
		self.assertEqual(type(item), ScribbledNote)
		self.assertEqual(item.text, 'beware of dog')
		self.assertEqual(pos, Point(1, 1))
	def should_save_item_at_pos(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		item = ScribbledNote('beware of dog')
		item = items.ItemAtPos(Point(1, 1), item)
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ScribbledNote\x00beware of dog\x001\x001')
