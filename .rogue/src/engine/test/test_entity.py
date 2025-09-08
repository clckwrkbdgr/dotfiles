from clckwrkbdgr import unittest
from .. import entity
from .. import items, ui

make_weapon = entity.MakeEntity(items.Item, '_sprite _name _attack')
MadeWeapon = make_weapon('Dagger', ui.Sprite('(', None), 'dagger', 1)

weapons_drop_uniform = entity.EntityClassDistribution(1)
weapons_drop_uniform << Dagger
weapons_drop = entity.EntityClassDistribution(lambda depth: max(0, (depth-7)//2))
weapons_drop << Dagger

class TestEntityBuilder(unittest.TestCase):
	def should_make_entity(self):
		dagger = Dagger()
		self.assertTrue(isinstance(dagger, items.Item))
		self.assertEqual(dagger.sprite.sprite, '(')
		self.assertEqual(dagger.name, 'dagger')
		self.assertEqual(dagger.attack, 1)

class TestEntityDistribution(unittest.TestCase):
	def should_distribute_entities_in_uniform_manner(self):
		self.assertEqual(list(weapons_drop_uniform), [Dagger])
		self.assertEqual(weapons_drop_uniform.get_distribution(0), [(1, Dagger)])
		self.assertEqual(weapons_drop_uniform.get_distribution(1), [(1, Dagger)])
		self.assertEqual(weapons_drop_uniform.get_distribution(16), [(1, Dagger)])
	def should_distribute_entities_based_on_depth(self):
		self.assertEqual(weapons_drop.get_distribution(0), [(0, Dagger)])
		self.assertEqual(weapons_drop.get_distribution(1), [(0, Dagger)])
		self.assertEqual(weapons_drop.get_distribution(7), [(0, Dagger)])
		self.assertEqual(weapons_drop.get_distribution(10), [(1, Dagger)])
		self.assertEqual(weapons_drop.get_distribution(16), [(4, Dagger)])
