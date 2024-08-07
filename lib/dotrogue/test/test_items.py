import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from ..math import Point
from .. import items

class TestItemTypes(unittest.TestCase):
	def should_str_item_type(self):
		self.assertEqual(str(items.ItemType('name', '!', items.Effect.NONE)), 'name')

class TestItems(unittest.TestCase):
	def should_str_item(self):
		item_type = items.ItemType('name', '!', items.Effect.NONE)
		item = items.Item(item_type, Point(1, 1))
		self.assertEqual(str(item), 'name @Point(x=1, y=1)')
