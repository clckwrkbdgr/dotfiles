import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point, Size, Rect
from clckwrkbdgr.pcg import RNG
from ..pcg import builders
from ..engine import items
from .. import engine
from .. import pcg
from .. import game
import clckwrkbdgr.serialize.stream as savefile
from . import mock_dungeon
from .mock_dungeon import MockGame

class AbstractTestDungeon(unittest.TestCase):
	def _formatMessage(self, msg, standardMsg): # pragma: no cover
		if hasattr(self, 'dungeon'):
			msg = (msg or '') + '\n' + self.dungeon.scene.tostring(self.dungeon.scene.get_area_rect())
		return super(AbstractTestDungeon, self)._formatMessage(msg, standardMsg)
	def _events(self):
		return [list(repr(event) for callback, event in self.dungeon.process_events(raw=True, bind_self=self))]

class TestMainDungeonLoop(AbstractTestDungeon):
	def should_run_main_loop(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(self._events(), [[
			]])
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP)
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'Move(actor=player, dest=[9, 5])',
			]])
		dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN)
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'Move(actor=player, dest=[9, 6])',
			]])
		dungeon.descend(dungeon.get_player())
		self.assertEqual(self._events(), [[
			'CannotDescend(pos=[9, 6])',
			]])
		dungeon.automove(Point(11, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # walking...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # walking...
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(self._events(), [[ # NONE AUTOEXPLORE
			'Move(actor=player, dest=[10, 5])',
			'Move(actor=player, dest=[11, 4])',
			'Discover(obj=stairs)',
			]])
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(self._events(), [[ # exploring...
			]])
		dungeon.automove()
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement())
		dungeon.stop_automovement()
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(self._events(), [[
			'Move(actor=player, dest=[11, 3])',
			'Move(actor=player, dest=[10, 2])',
			'Move(actor=player, dest=[11, 3])',
			'Move(actor=player, dest=[12, 4])',
			'Move(actor=player, dest=[13, 3])',
			'Move(actor=player, dest=[12, 4])',
			'Move(actor=player, dest=[11, 4])',
			'Move(actor=player, dest=[10, 4])',
			'Move(actor=player, dest=[9, 4])',
			]])
		dungeon.automove()
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.in_automovement())
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(self._events(), [[ # GOD_TOGGLE_* EXIT
			'Move(actor=player, dest=[8, 3])',
			'Move(actor=player, dest=[7, 2])',
			'Move(actor=player, dest=[6, 2])',
			'Move(actor=player, dest=[5, 2])',
			]])
		dungeon.god.toggle_vision()
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(self._events(), [[
			]])
		dungeon.god.toggle_noclip()
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(self._events(), [[
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_perform_monsters_turns_after_player_has_done_with_their_turn(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		self.assertEqual(self._events(), [[
			'Discover(obj=monster)',
			'Discover(obj=monster)',
			]])
		self.assertEqual(self._events(), [[
			]])
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP) # Step in.
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'Move(actor=player, dest=[9, 5])',
			'Attack(actor=monster, target=player, damage=1)',
			'Health(target=player, diff=-1)',
			]])
		self.assertEqual(self._events(), [[
			]])
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP) # Attack.
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'Attack(actor=player, target=monster, damage=1)',
			'Health(target=monster, diff=-1)',
			'Attack(actor=monster, target=player, damage=1)',
			'Health(target=player, diff=-1)',
			]])
		dungeon.wait(dungeon.get_player()) # Just wait.
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'Attack(actor=monster, target=player, damage=1)',
			'Health(target=player, diff=-1)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
		self.assertEqual(dungeon.get_player().hp, 7)
		self.assertEqual(dungeon.scene.monsters[2].hp, 2)

class TestItems(AbstractTestDungeon):
	def should_grab_items(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around 2')
		self.assertEqual(self._events(), [[
			'Discover(obj=potion)',
			'Discover(obj=healing potion)',
			]])
		dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'Move(actor=player, dest=[10, 6])',
			]])
		dungeon.grab_item_here(dungeon.get_player())
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'GrabItem(actor=player, item=potion)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_drop_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(mock_dungeon.Potion())
		self.assertEqual(self._events(), [[
			]])
		dungeon.drop_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		dungeon.process_others()
		self.assertEqual(self._events(), [[
			'DropItem(actor=player, item=potion)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None

class TestVisibility(AbstractTestDungeon):
	def should_get_visible_surroundings(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.scene.get_area_rect(), Rect(Point(0, 0), Size(20, 10)))
		self.assertEqual(dungeon.str_cell(Point(9, 6)), '@')
		self.assertEqual(dungeon.str_cell(Point(5, 6)), '.')
		self.assertEqual(dungeon.str_cell(Point(5, 5)), '#')
		self.assertEqual(dungeon.str_cell(Point(10, 1)), ' ')
		dungeon.jump_to(dungeon.scene.get_player(), Point(11, 2))
		self.assertEqual(dungeon.str_cell(Point(9, 6)), '.')
		self.assertEqual(dungeon.str_cell(Point(5, 6)), ' ')
		self.assertEqual(dungeon.str_cell(Point(5, 5)), '#')
		self.assertEqual(dungeon.str_cell(Point(10, 1)), '>')
		dungeon.jump_to(dungeon.scene.get_player(), Point(9, 6))
		self.assertEqual(dungeon.str_cell(Point(10, 1)), '>')
	def should_get_visible_monsters_and_items(self):
		dungeon = self.dungeon = mock_dungeon.build('monsters on top')
		dungeon.jump_to(dungeon.scene.get_player(), Point(2, 2))
		self.assertEqual(dungeon.str_cell(Point(1, 1)), 'M')
		self.assertEqual(dungeon.str_cell(Point(1, 6)), 'M')
		self.assertEqual(dungeon.str_cell(Point(2, 6)), '!')
		dungeon.jump_to(dungeon.scene.get_player(), Point(10, 1))
		self.assertEqual(dungeon.str_cell(Point(1, 1)), ' ')
		self.assertEqual(dungeon.str_cell(Point(1, 6)), ' ')
		self.assertEqual(dungeon.str_cell(Point(2, 6)), ' ')
	def should_see_monsters_only_in_the_field_of_vision(self):
		dungeon = self.dungeon = mock_dungeon.build('now you see me')
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				    #####        #  
				     ....   #  ...  
				      ...  .# ..... 
				     ##..##.#...... 
				     #............. 
				#....#............. 
				#M.......@.........#
				#.................. 
				#.................. 
				 #################  
				"""))
		dungeon.jump_to(dungeon.scene.get_player(), Point(2, 2))
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				##########       #  
				#M.......#  #       
				#.@......#  #       
				#....##..## #       
				#....#              
				#....#              
				#M....             #
				#......             
				#.......            
				##################  
				"""))
	def should_reduce_visibility_at_dark_tiles(self):
		dungeon = self.dungeon = mock_dungeon.build('mini dark rogue')
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+   
				_ |@.|   
				_ ^..^   
				_ |.>|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN)
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+   
				_ |..|   
				_ ^.@^   
				_ |.>|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+   
				_ |..|   
				_ ^..@#  
				_ |.>|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+   
				_ |  | # 
				_ ^  ^@# 
				_ | >|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+   
				_ |  | # 
				_ ^  ^#@ 
				_ | >|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP)
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+ # 
				_ |  | @ 
				_ ^  ^## 
				_ | >|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP)
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				_ +--+ @ 
				_ |  | # 
				_ ^  ^   
				_ | >|   
				_ +--+   
				""").replace('_', ' '))

class TestMovement(AbstractTestDungeon):
	def should_update_fov_after_movement(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertFalse(dungeon.vision.visited.cell(dungeon.scene.appliances[0].pos))
		self.maxDiff = None
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				    #####        #  
				     ....   #  ...  
				      ...  .# ..... 
				     ##..##.#...... 
				     #............. 
				#....#............. 
				#........@.........#
				#.................. 
				#.................. 
				 #################  
				"""))
		dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT) 
		self.assertFalse(dungeon.vision.visited.cell(dungeon.scene.appliances[0].pos))
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				    #####      #### 
				     ...   ## ..... 
				      ...  .#......#
				     ##..##.#......#
				     #.............#
				#    #.............#
				#.........@........#
				#..................#
				#..................#
				 ################## 
				"""))
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP_RIGHT) 
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP) 
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP) 
		dungeon.move_actor(dungeon.get_player(), game.Direction.UP) 
		self.assertTrue(dungeon.vision.visited.cell(dungeon.scene.appliances[0].pos))
		self.assertEqual(dungeon.tostring(dungeon.scene.get_area_rect()), textwrap.dedent("""\
				   ########    #####
				         #>##      #
				         #.@#      #
				     ##  ##.#      #
				     #    ...      #
				#    #    ...      #
				#        .....     #
				#        .....     #
				#       .......    #
				 ###################
				"""))
	def should_not_allow_move_player_diagonally_both_from_and_to_good_cell(self):
		dungeon = self.dungeon = mock_dungeon.build('mini rogue lonely')
		self.assertEqual(dungeon.get_player().pos, Point(3, 1))

		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move_actor(dungeon.get_player(), game.Direction.UP_RIGHT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.UP))
		self.assertEqual(dungeon.get_player().pos, Point(7, 1))
		self.assertFalse(dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.LEFT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.LEFT))
		self.assertFalse(dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.LEFT))
		self.assertTrue(dungeon.move_actor(dungeon.get_player(), game.Direction.DOWN))
		self.assertEqual(dungeon.get_player().pos, Point(4, 3))

class TestFight(AbstractTestDungeon):
	def should_angry_move_to_attack_player(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster')
		list(dungeon.process_events(raw=True))

		monster = dungeon.scene.monsters[-1]
		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.scene.monsters[-1].pos, Point(10, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), engine.Events.Move)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].dest, Point(10, 6))
		list(dungeon.process_events(raw=True))

		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), engine.Events.Attack)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].target, dungeon.get_player())
		self.assertEqual(type(dungeon.events[1]), engine.Events.Health)
		self.assertEqual(dungeon.events[1].target, dungeon.get_player())
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_not_angry_move_when_player_is_out_of_sight(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster 2')
		list(dungeon.process_events(raw=True))

		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.scene.monsters[-1].pos, Point(4, 4))
		self.assertEqual(len(dungeon.events), 0)
