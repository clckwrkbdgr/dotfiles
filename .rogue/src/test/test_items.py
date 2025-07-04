import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point
from .. import items
import clckwrkbdgr.serialize.stream as savefile
from ..defs import Version
from . import mock_dungeon

class MockItem(items.Item):
	name = 'name'
	sprite = '!'

class TestItems(unittest.TestCase):
	def should_str_item(self):
		item = MockItem()
		self.assertEqual(str(item), 'name')
		item = items.ItemAtPos(Point(1, 1), item)
		self.assertEqual(str(item), 'name @[1, 1]')

class TestSavefile(unittest.TestCase):
	def should_load_item(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name')
		reader = savefile.Reader(stream)
		reader.set_meta_info('ITEMS', mock_dungeon.MockGame.ITEMS)
		item = reader.read(items.Item)
		self.assertEqual(type(item), mock_dungeon.MockGame.ITEMS['name'])
	def should_save_item(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		item = mock_dungeon.MockGame.ITEMS['name']()
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00NameItem')
	def should_load_item_at_pos(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x001\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('ITEMS', mock_dungeon.MockGame.ITEMS)
		reader.set_meta_info('ItemClass', items.Item)
		pos, item = reader.read(items.ItemAtPos)
		self.assertEqual(type(item), mock_dungeon.MockGame.ITEMS['name'])
		self.assertEqual(pos, Point(1, 1))
	def should_save_item_at_pos(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		item = mock_dungeon.MockGame.ITEMS['name']()
		item = items.ItemAtPos(Point(1, 1), item)
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00NameItem\x001\x001')
