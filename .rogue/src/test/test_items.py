import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from ..math import Point
from .. import items
from ..system import savefile
from ..defs import Version

class TestItemTypes(unittest.TestCase):
	def should_str_item_type(self):
		self.assertEqual(str(items.ItemType('name', '!', items.Effect.NONE)), 'name')

class TestItems(unittest.TestCase):
	def should_str_item(self):
		item_type = items.ItemType('name', '!', items.Effect.NONE)
		item = items.Item(item_type, Point(1, 1))
		self.assertEqual(str(item), 'name @1;1')

class TestSavefile(unittest.TestCase):
	def setUp(self):
		self.ITEMS = {
				'name' : items.ItemType('name', '!', items.Effect.NONE),
				}
	def should_load_item(self):
		stream = StringIO(str(Version.CURRENT) + '\x00name\x001\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('ITEMS', self.ITEMS)
		item = reader.read(items.Item)
		self.assertEqual(item.item_type, self.ITEMS['name'])
		self.assertEqual(item.pos, Point(1, 1))
	def should_save_item(self):
		stream = StringIO()
		writer = savefile.Writer(stream, Version.CURRENT)
		item = items.Item(self.ITEMS['name'], Point(1, 1))
		writer.write(item)
		self.assertEqual(stream.getvalue(), str(Version.CURRENT) + '\x00name\x001\x001')
