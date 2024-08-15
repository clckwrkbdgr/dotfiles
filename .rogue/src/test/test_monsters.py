import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from ..math import Point
from .. import monsters

class TestSpecies(unittest.TestCase):
	def should_str_species(self):
		self.assertEqual(str(monsters.Species('name', '@', 100, vision=10)), 'name 100hp')

class TestMonsters(unittest.TestCase):
	def should_str_monster(self):
		species = monsters.Species('name', '@', 100, vision=10)
		monster = monsters.Monster(species, monsters.Behavior.ANGRY, Point(1, 1))
		self.assertEqual(str(monster), 'name @Point(x=1, y=1) 100/100hp')
