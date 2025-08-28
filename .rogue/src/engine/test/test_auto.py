from clckwrkbdgr import unittest
from .._base import Events
from .. import auto
from ..mock import *
from .utils import *

class TestAutoMode(AbstractTestDungeon):
	def should_auto_walk_to_position(self):
		dungeon = self.game
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 5))

		self.assertFalse(dungeon.perform_automovement())
		dungeon.automove(Point(2, 3))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		self.assertFalse(dungeon.perform_automovement()) # You have reached your destination.
		self.assertFalse(dungeon.perform_automovement()) # No more automovement left.

		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), unittest.dedent("""\
				_        _
				#....    _
				#?.&.    _
				#.@..    _
				#....    _
				#<...    _
				##  >    _
				#        _
				_        _
				_        _
				""").replace('_', ' '))
	def should_stop_automovement_on_event(self):
		dungeon = self.game
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 5))

		dungeon.automove(Point(4, 8)) # No path there; cannot see the dest.
		self.assertFalse(dungeon.perform_automovement())

		dungeon.automove(Point(3, 7))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.events, [
			Events.Move(dungeon.scene.get_player(), Point(2, 6)),
			Events.Discover(next(dungeon.scene.iter_actors_at(Point(3, 8)))),
			])

		list(dungeon.process_events(raw=True)) # Clear events.
		self.assertFalse(dungeon.perform_automovement()) # Startled by butterfly.
		self.assertEqual(dungeon.events, [
			])

		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), unittest.dedent("""\
				_        _
				         _
				         _
				#        _
				#....    _
				#<...    _
				##@~>    _
				#....    _
				#..b.    _
				_        _
				""").replace('_', ' '))
	def should_continue_autoexplore(self):
		dungeon = NanoDungeon()
		dungeon.generate(None)
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 5))

		dungeon.automove()
		for _ in range(11):
			list(dungeon.process_events(raw=True)) # Clear events.
			self.assertTrue(dungeon.perform_automovement())
		self.assertFalse(dungeon.perform_automovement()) # You have reached your destination.
		self.assertEqual(dungeon.events, [
			Events.Move(dungeon.scene.get_player(), Point(2, 6)),
			Events.Discover(next(dungeon.scene.iter_actors_at(Point(3, 8)))),
			])

		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), unittest.dedent("""\
				#######  _
				#        _
				#  &     _
				#        _
				#....    _
				#<...    _
				##@~>    _
				#....    _
				#..b.    _
				_        _
				""").replace('_', ' '))
	def should_stop_autoexplore_when_nothing_left(self):
		dungeon = NanoDungeon()
		dungeon.generate(None)
		dungeon.scene.monsters.pop(0) # butterfly
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 5))

		dungeon.automove()
		for _ in range(28):
			list(dungeon.process_events(raw=True)) # Clear events.
			self.assertTrue(dungeon.perform_automovement())
		self.assertFalse(dungeon.perform_automovement()) # You have reached your destination.
		self.assertEqual(dungeon.events, [
			Events.Move(dungeon.scene.get_player(), Point(7, 7)),
			])

		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), unittest.dedent("""\
				##########
				#        #
				#  &     #
				#        #
				#        #
				#<   ....#
				##  >....#
				#    ..@.#
				#    ....#
				##########
				""").replace('_', ' '))
