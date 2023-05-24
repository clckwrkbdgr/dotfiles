from ...math import Point
from ... import unittest
from .. import dungeon as rogue_dungeon

class TestDungeon(unittest.TestCase):
	@unittest.mock.patch('random.randrange', side_effect=[1, 1, 0, 1] + [24, 24] * 250)
	def should_generate_random_dungeon(self, random_randrange):
		dungeon = rogue_dungeon.Dungeon()
		self.assertEqual(dungeon.terrain.width, 25)
		self.assertEqual(dungeon.terrain.height, 25)
		self.assertEqual(dungeon.terrain.cell((0, 0)), '.')
		self.assertEqual(dungeon.terrain.cell((1, 0)), '.')
		self.assertEqual(dungeon.terrain.cell((0, 1)), '#')
		self.assertEqual(dungeon.terrain.cell((1, 1)), '#')
		self.assertEqual(dungeon.rogue, (12, 12))
	@unittest.mock.patch('random.randrange', side_effect=[1, 1, 0, 1] + [24, 24] * 250)
	def should_get_dungeon_sprites_for_view(self, random_randrange):
		dungeon = rogue_dungeon.Dungeon()
		self.assertEqual(dungeon.get_sprite((0, 0)), '.')
		self.assertEqual(dungeon.get_sprite((1, 0)), '.')
		self.assertEqual(dungeon.get_sprite((0, 1)), '#')
		self.assertEqual(dungeon.get_sprite((1, 1)), '#')
		self.assertEqual(dungeon.get_sprite((12, 12)), '@')
	@unittest.mock.patch('random.randrange', side_effect=[1, 1, 0, 1] + [24, 24] * 250)
	def should_move_player(self, random_randrange):
		dungeon = rogue_dungeon.Dungeon()
		self.assertEqual(dungeon.rogue, (12, 12))
		dungeon.control(Point(0, 1))
		self.assertEqual(dungeon.rogue, (12, 13))
	@unittest.mock.patch('random.randrange', side_effect=[24, 24] * 250)
	def should_not_move_player_outside_the_map(self, random_randrange):
		dungeon = rogue_dungeon.Dungeon()
		self.assertEqual(dungeon.rogue, (12, 12))
		for _ in range(13):
			dungeon.control(Point(0, -1))
		self.assertEqual(dungeon.rogue, (12, 0))
	@unittest.mock.patch('random.randrange', side_effect=[12, 11] + [24, 24] * 250)
	def should_not_move_player_into_wall(self, random_randrange):
		dungeon = rogue_dungeon.Dungeon()
		self.assertEqual(dungeon.rogue, (12, 12))
		dungeon.control(Point(0, -1))
		self.assertEqual(dungeon.rogue, (12, 12))
	@unittest.mock.patch('random.randrange', side_effect=[24, 24] * 250)
	def should_raise_given_game_exception(self, random_randrange):
		dungeon = rogue_dungeon.Dungeon()
		class MockEvent(Exception): pass
		with self.assertRaises(MockEvent):
			dungeon.control(MockEvent)
		with self.assertRaises(MockEvent):
			dungeon.control(MockEvent())
