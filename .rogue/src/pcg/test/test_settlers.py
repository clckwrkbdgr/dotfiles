import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from .. import settlers, builders
from ... import monsters
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.pcg import RNG

class TestSquatters(unittest.TestCase):
	def _make_terrain(self, builder):
		from ...game import Game # FIXME circular dependency
		from ...terrain import Cell, Terrain # FIXME circular dependency
		builder.map_key(**({
				'void' : Cell(Terrain('void', " ", False, remembered=' ')),
				'corner' : Cell(Terrain('corner', "+", False, remembered='+')),
				'rogue_door' : Cell(Terrain('rogue_door', "+", True, remembered='+', allow_diagonal=False, dark=True)),
				'floor' : Cell(Terrain('floor', ".", True)),
				'rogue_passage' : Cell(Terrain('rogue_passage', "#", True, remembered='#', allow_diagonal=False, dark=True)),
				'wall_h' : Cell(Terrain('wall_h', "-", False, remembered='-')),
				'wall_v' : Cell(Terrain('wall_v', "|", False, remembered='|')),
				}))
		return builder.make_grid()
	def should_populate_dungeon_with_squatters(self):
		rng = RNG(0)
		class _MockSquatters(settlers.RogueDungeonSquatters):
			class Mapping:
				rodent = staticmethod(lambda pos,*data: ('rodent',) + data + (pos,))
				plant = staticmethod(lambda pos,*data: ('plant',) + data + (pos,))
				slime = staticmethod(lambda pos,*data: ('slime',) + data + (pos,))
				healing_potion = staticmethod(lambda pos,*data: ('healing potion',) + data + (pos,))
			MONSTERS = [
					('plant', monsters.Behavior.DUMMY),
					('slime', monsters.Behavior.INERT),
					('rodent', monsters.Behavior.ANGRY),
					]
			ITEMS = [
					('healing_potion',),
					]
			PASSABLE = ('floor',)
		builder = _MockSquatters(rng, Size(80, 25))
		builder.generate()
		settler = builder
		self._make_terrain(builder)
		_monsters = list(builder.make_actors())
		_items = list(builder.make_items())

		self.maxDiff = None
		self.assertEqual(sorted(_monsters), sorted([
			('rodent', 3, Point(59, 18)),
			('plant', 1,  Point(68, 12)),
			('rodent', 3, Point(33, 9)),
			('plant', 1,  Point(34, 11)),
			('rodent', 3, Point(9, 19)),
			('plant', 1,  Point(65, 11))
			]))
		self.assertEqual(sorted(_items), sorted([
			('healing potion', Point(31, 19)),
			('healing potion', Point(61, 3)),
			]))
	def should_populate_dungeon_with_weighted_squatters(self):
		rng = RNG(0)
		class _MockSquatters(settlers.RogueDungeonWeightedSquatters):
			class Mapping:
				rodent = staticmethod(lambda pos,*data: ('rodent',) + data + (pos,))
				plant = staticmethod(lambda pos,*data: ('plant',) + data + (pos,))
				slime = staticmethod(lambda pos,*data: ('slime',) + data + (pos,))
				healing_potion = staticmethod(lambda pos,*data: ('healing potion',) + data + (pos,))
			MONSTERS = [
					(1, 'plant', monsters.Behavior.DUMMY),
					(5, 'slime', monsters.Behavior.INERT),
					(10, 'rodent', monsters.Behavior.ANGRY),
					]
			ITEMS = [
					(1, 'healing_potion',),
					]
			PASSABLE = ('floor',)
		builder = _MockSquatters(rng, Size(80, 25))
		builder.generate()
		settler = builder
		self._make_terrain(builder)
		_monsters = list(builder.make_actors())
		_items = list(builder.make_items())

		self.maxDiff = None
		self.assertEqual(sorted(_monsters), sorted([
			('rodent', 3, Point(59, 18)),
			('slime', 2,  Point(68, 12)),
			('rodent', 3, Point(33, 9)),
			('slime', 2,  Point(34, 11)),
			('rodent', 3, Point(9, 19)),
			('slime', 2,  Point(65, 11))
			]))
		self.assertEqual(sorted(_items), sorted([
			('healing potion', Point(61, 3)),
			('healing potion', Point(63, 4)),
			]))
