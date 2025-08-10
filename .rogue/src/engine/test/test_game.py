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
		game.generate()

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
