from clckwrkbdgr import unittest
from .. import items

class MockPotion(items.Item):
	_sprite = '!'
	_name = 'potion'

class TestItems(unittest.TestCase):
	def should_str_item(self):
		potion = MockPotion()
		self.assertEqual(str(potion), 'potion')
		self.assertEqual(repr(potion), 'MockPotion(potion)')
