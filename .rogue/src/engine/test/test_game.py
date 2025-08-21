from clckwrkbdgr import unittest
from .. import _base
from .. import events
from ..mock import *

class TestEvents(unittest.TestCase):
	def should_process_events(self):
		game = _base.Game()
		game.fire_event(DropItem(who='me', where='floor', what='something'))
		self.assertEqual(list(game.process_events()), [
			'me drops something on floor',
			])

class TestActionLoop(unittest.TestCase):
	def should_process_others(self):
		game = NanoDungeon()
		game.generate(None)

		self.assertFalse(game.scene.get_player().has_acted())
		game.process_others()
		self.assertEqual(game.playing_time, 0)
		self.assertEqual(list(game.process_events()), [])

		game.scene.get_player().spend_action_points()
		self.assertTrue(game.scene.get_player().has_acted())
		game.process_others()
		self.assertEqual(game.playing_time, 1)
		self.assertFalse(game.scene.get_player().has_acted())
		self.assertEqual(list(game.process_events()), [
			'butterfly flops its wings',
			])

class TestVision(unittest.TestCase):
	def should_see_places(self):
		game = NanoDungeon()
		game.generate(None)
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size), visited=False), unittest.dedent("""\
				__________
				__________
				__________
				#...______
				#...______
				#@..______
				##.~______
				#...______
				__________
				__________
				""").replace('_', ' '))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size), visited=False), unittest.dedent("""\
				__________
				__________
				__________
				__________
				__________
				__________
				__.~>..___
				__.....___
				__.b@..___
				__#####___
				""").replace('_', ' '))
	def should_remember_places(self):
		game = NanoDungeon()
		game.generate(None)
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				__________
				__________
				__________
				#...______
				#...______
				#@..______
				##.~______
				#...______
				__________
				__________
				""").replace('_', ' '))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				__________
				__________
				__________
				#   ______
				#    _____
				#<    ____
				##.~>..___
				# .....___
				# .b@..___
				_######___
				""").replace('_', ' '))

class TestMovement(unittest.TestCase):
	def should_move_actor(self):
		game = NanoDungeon()
		game.generate(None)
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.Move(game.scene.get_player(), Point(2, 6))])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#<.......#
				##@~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_bump_into_terrain(self):
		game = NanoDungeon()
		game.generate(None)
		self.assertFalse(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.BumpIntoTerrain(game.scene.get_player(), Point(1, 6))])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#@.......#
				##.~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_attack_other_actor(self):
		game = NanoDungeon()
		game.generate(None)
		game.scene.transfer_actor(game.scene.get_player(), Point(3, 7))
		self.assertFalse(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.BumpIntoActor(game.scene.get_player(), next(_ for _ in game.scene.monsters if _.name == 'butterfly'))])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#<.......#
				##.~>....#
				#..@.....#
				#..b.....#
				##########
				"""))

class TestScenes(unittest.TestCase):
	def should_travel_to_other_scene(self):
		game = NanoDungeon()
		game.generate('floor')
		self.assertEqual(len(game.scenes), 1)

		game.travel(game.scene.get_player(), 'tomb', 'enter')
		self.assertEqual(game.current_scene_id, 'tomb')
		self.assertEqual(len(game.scenes), 2)
		self.assertEqual(game.scene.get_player().pos, Point(1, 1))
