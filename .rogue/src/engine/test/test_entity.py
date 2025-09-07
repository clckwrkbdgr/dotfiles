from clckwrkbdgr import unittest
from .. import entity
from .. import items, ui

make_weapon = entity.MakeEntity(items.Item, '_sprite _name _attack')
MadeWeapon = make_weapon('Dagger', ui.Sprite('(', None), 'dagger', 1)

class TestItems(unittest.TestCase):
	def should_make_entity(self):
		dagger = Dagger()
		self.assertTrue(isinstance(dagger, items.Item))
		self.assertEqual(dagger.sprite.sprite, '(')
		self.assertEqual(dagger.name, 'dagger')
		self.assertEqual(dagger.attack, 1)
