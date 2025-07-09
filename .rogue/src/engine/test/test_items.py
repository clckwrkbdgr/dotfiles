from clckwrkbdgr import unittest
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.math import Point
from .. import items

VERSION = 666

class MockPotion(items.Item):
	_sprite = '!'
	_name = 'potion'

class ColoredPotion(items.Item):
	_sprite = '.'
	_name = 'potion'
	def __init__(self, color='transparent'):
		self.color = color
	def load(self, stream):
		self.color = stream.read()
	def save(self, stream):
		super(ColoredPotion, self).save(stream)
		stream.write(self.color)

class TestItems(unittest.TestCase):
	def should_str_item(self):
		potion = MockPotion()
		self.assertEqual(str(potion), 'potion')
		self.assertEqual(repr(potion), 'MockPotion(potion)')
	def should_str_item_at_pos(self):
		potion = MockPotion()
		item = items.ItemAtPos(Point(1, 1), potion)
		self.assertEqual(str(item), 'potion @[1, 1]')

class TestItemsSavefile(unittest.TestCase):
	def should_load_item(self):
		stream = StringIO(str(VERSION) + '\x00MockPotion')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Items', {'MockPotion':MockPotion})
		item = reader.read(items.Item)
		self.assertEqual(type(item), MockPotion)
	def should_save_item(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		item = MockPotion()
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00MockPotion')
	def should_load_item_with_custom_properties(self):
		stream = StringIO(str(VERSION) + '\x00ColoredPotion\x00red')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Items', {'ColoredPotion':ColoredPotion})
		item = reader.read(items.Item)
		self.assertEqual(type(item), ColoredPotion)
		self.assertEqual(item.color, 'red')
	def should_save_item_with_custom_properties(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		item = ColoredPotion('red')
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ColoredPotion\x00red')

class TestItemAtPosSavefile(unittest.TestCase):
	def should_load_item_at_pos(self):
		stream = StringIO(str(VERSION) + '\x00ColoredPotion\x00red\x001\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('Items', {'ColoredPotion':ColoredPotion})
		pos, item = reader.read(items.ItemAtPos)
		self.assertEqual(type(item), ColoredPotion)
		self.assertEqual(item.color, 'red')
		self.assertEqual(pos, Point(1, 1))
	def should_save_item_at_pos(self):
		stream = StringIO()
		writer = savefile.Writer(stream, VERSION)
		item = ColoredPotion('red')
		item = items.ItemAtPos(Point(1, 1), item)
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(VERSION) + '\x00ColoredPotion\x00red\x001\x001')
