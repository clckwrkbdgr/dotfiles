import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from ..math import Point
from .. import monsters
from ..pcg import RNG

class TestSpecies(unittest.TestCase):
	def should_str_species(self):
		self.assertEqual(str(monsters.Species('name', '@', 100, vision=10)), 'name 100hp')

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		species = monsters.Species('name', '@', 100, vision=10)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(str(monster), 'name @Point(x=1, y=1) 100/100hp')
	def should_not_drop_items(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=None)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster.drop_loot(rng), [])
	def should_drop_items(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=[
			(1, 'potion'),
			(2, 'money'),
			(3, 'rags'),
			])
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster.drop_loot(rng), [('potion',)])
		self.assertEqual(monster.drop_loot(rng), [('rags',)])
		self.assertEqual(monster.drop_loot(rng), [('money',)])
		self.assertEqual(monster.drop_loot(rng), [('rags',)])
		self.assertEqual(monster.drop_loot(rng), [('potion',)])
	def should_drop_nothing_sometimes(self):
		rng = RNG(0)
		species = monsters.Species('name', '@', 100, vision=10, drops=[
			(1, None),
			(2, 'money'),
			(3, None),
			])
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(monster.drop_loot(rng), [])
		self.assertEqual(monster.drop_loot(rng), [])
		self.assertEqual(monster.drop_loot(rng), [('money',)])
		self.assertEqual(monster.drop_loot(rng), [])
		self.assertEqual(monster.drop_loot(rng), [])
