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

class TestActions(unittest.TestCase):
	def should_suicide(self):
		game = NanoDungeon()
		game.generate(None)
		game.suicide(game.scene.get_player())
		self.assertFalse(game.scene.get_player())

class TestMovement(unittest.TestCase):
	def should_wait_in_place(self):
		game = NanoDungeon()
		game.generate(None)
		game.wait(game.scene.get_player())
		self.assertTrue(game.scene.get_player().has_acted())
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
	def should_not_move_into_void(self):
		game = NanoDungeon()
		game.generate(None)
		game.scene.get_player().pos = Point(0, 6)
		self.assertFalse(game.move_actor(game.scene.get_player(), Point(-1, 0)))
		self.assertFalse(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.StareIntoVoid()])
	def should_walk_through_terrain_in_noclip_mode(self):
		game = NanoDungeon()
		game.generate(None)
		game.god.noclip = True
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.Move(game.scene.get_player(), Point(1, 6))])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#<.......#
				#@.~>....#
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

class TestInventory(unittest.TestCase):
	def should_drop_item(self):
		game = NanoDungeon()
		game.generate(None)
		dagger = game.scene.get_player().inventory[0]
		game.drop_item(game.scene.get_player(), dagger)
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(list(game.scene.iter_items_at((1, 5))), [dagger])
		self.assertFalse(game.scene.get_player().inventory)
		self.assertEqual(game.events, [_base.Events.DropItem(game.scene.get_player(), dagger)])
		game.scene.get_player().pos = Point(2, 6)
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#(.......#
				##@~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_grab_item(self):
		game = NanoDungeon()
		game.generate(None)

		game.grab_item_here(game.scene.get_player())
		self.assertEqual(game.events, [_base.Events.NothingToPickUp()])
		self.assertFalse(game.scene.get_player().has_acted())

		list(game.process_events(raw=True)) # Clear events.
		game.scene.get_player().pos = Point(1, 2)
		game.grab_item_here(game.scene.get_player())
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(list(game.scene.iter_items_at((1, 5))), [])
		scroll = game.scene.get_player().find_item(ScribbledNote)
		self.assertIsNotNone(scroll)
		self.assertEqual(game.events, [_base.Events.GrabItem(game.scene.get_player(), scroll)])
		game.scene.get_player().pos = Point(2, 2)
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#.@&.....#
				#........#
				#........#
				#<.......#
				##.~>....#
				#........#
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
