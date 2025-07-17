import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.pcg import RNG
from ..pcg import builders
from ..engine import items
from .. import pcg
from .. import game
from .. import ui
import clckwrkbdgr.serialize.stream as savefile
from . import mock_dungeon
from .mock_dungeon import MockGame

class MockWriterStream:
	def __init__(self):
		self.dump = []
	def write(self, item):
		if item == '\0':
			return
		self.dump.append(item)

class AbstractTestDungeon(unittest.TestCase):
	def _formatMessage(self, msg, standardMsg): # pragma: no cover
		if hasattr(self, 'dungeon'):
			msg = (msg or '') + '\n' + self.dungeon.tostring()
		return super(AbstractTestDungeon, self)._formatMessage(msg, standardMsg)
	def _events(self):
		return [list(repr(event) for callback, event in self.dungeon.process_events(raw=True, bind_self=self))]

class TestMainDungeonLoop(AbstractTestDungeon):
	def should_run_main_loop(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'MoveEvent(actor=player, dest=[9, 5])',
			]])
		dungeon.move(dungeon.get_player(), game.Direction.DOWN)
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'MoveEvent(actor=player, dest=[9, 6])',
			]])
		dungeon.descend()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.walk_to(Point(11, 2))
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # walking...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # walking...
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[ # NONE AUTOEXPLORE
			'DiscoverEvent(obj=>)',
			]])
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[ # exploring...
			]])
		dungeon.start_autoexploring()
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement()) # exploring...
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement())
		dungeon.autostop()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.start_autoexploring()
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(dungeon._pre_action())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[ # GOD_TOGGLE_* EXIT
			]])
		dungeon.toggle_god_vision()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.toggle_god_noclip()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_perform_monsters_turns_after_player_has_done_with_their_turn(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'DiscoverEvent(obj=monster)',
			'DiscoverEvent(obj=monster)',
			]])
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.move(dungeon.get_player(), game.Direction.UP) # Step in.
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'MoveEvent(actor=player, dest=[9, 5])',
			'AttackEvent(actor=monster, target=player)',
			'HealthEvent(target=player, diff=-1)',
			]])
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.move(dungeon.get_player(), game.Direction.UP) # Attack.
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'AttackEvent(actor=player, target=monster)',
			'HealthEvent(target=monster, diff=-1)',
			'AttackEvent(actor=monster, target=player)',
			'HealthEvent(target=player, diff=-1)',
			]])
		dungeon.wait() # Just wait.
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'AttackEvent(actor=monster, target=player)',
			'HealthEvent(target=player, diff=-1)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
		self.assertEqual(dungeon.get_player().hp, 7)
		self.assertEqual(dungeon.scene.monsters[2].hp, 2)
	def should_die_after_monster_attack(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'DiscoverEvent(obj=monster)',
			'DiscoverEvent(obj=monster)',
			]])
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.move(dungeon.get_player(), game.Direction.UP) # Step in.
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'MoveEvent(actor=player, dest=[9, 5])',
			'AttackEvent(actor=monster, target=player)'.format(9),
			'HealthEvent(target=player, diff=-1)'.format(9),
			]])
		dungeon.wait()
		dungeon.end_turn()
		for i in range(1, 9): # Just wait while monster kills you.
			self.assertTrue(dungeon._pre_action())
			self.assertEqual(self._events(), [[
				'AttackEvent(actor=monster, target=player)'.format(9 - i),
				'HealthEvent(target=player, diff=-1)'.format(9 - i),
				]])
			dungeon.wait()
			dungeon.end_turn()
		self.assertFalse(dungeon._pre_action())
		self.assertTrue(dungeon.is_finished())
		self.maxDiff = None
		self.assertIsNone(dungeon.get_player())
		self.assertEqual(dungeon.scene.monsters[1].hp, 3)
	def should_suicide_out_of_main_loop(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.suicide(dungeon.get_player())
		dungeon.end_turn()
		self.assertFalse(dungeon._pre_action())
		self.assertTrue(dungeon.is_finished())
		self.assertIsNone(dungeon.get_player())
		self.maxDiff = None

class TestItems(AbstractTestDungeon):
	def should_grab_items(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around 2')
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'DiscoverEvent(obj=potion)',
			'DiscoverEvent(obj=healing potion)',
			]])
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'MoveEvent(actor=player, dest=[10, 6])',
			]])
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'GrabItemEvent(actor=player, item=potion)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_consume_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(dungeon.ITEMS['potion']())
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.consume_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'ConsumeItemEvent(actor=player, item=potion)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_drop_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(dungeon.ITEMS['potion']())
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.drop_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'DropItemEvent(actor=player, item=potion)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_equip_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(dungeon.ITEMS['weapon']())
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.wield_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'EquipItemEvent(actor=player, item=weapon)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None
	def should_unequip_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().wielding = dungeon.ITEMS['weapon']()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			]])
		dungeon.unwield_item(dungeon.get_player())
		dungeon.end_turn()
		self.assertTrue(dungeon._pre_action())
		self.assertEqual(self._events(), [[
			'UnequipItemEvent(actor=player, item=weapon)',
			]])
		self.assertFalse(dungeon.is_finished())
		self.maxDiff = None

class TestEvents(AbstractTestDungeon):
	def should_notify_when_found_exit(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.events, [])
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), game.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, '>')
		list(dungeon.process_events(raw=True))
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(dungeon.events, [])
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(dungeon.events, [])
	def should_notify_when_see_monsters(self):
		dungeon = self.dungeon = mock_dungeon.build('now you see me')
		# At start we see just the one monster.
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), game.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.scene.monsters if monster.pos == Point(1, 6)))
		list(dungeon.process_events(raw=True))

		# Now we see both, but reporting only the new one.
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.scene.monsters if monster.pos == Point(1, 1)))
		list(dungeon.process_events(raw=True))

		# Now we see just the original one - visibility did not change.
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(dungeon.events, [])

		# Now we see both, but reporting only the new one again.
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.scene.monsters if monster.pos == Point(1, 1)))
		list(dungeon.process_events(raw=True))

class TestVisibility(AbstractTestDungeon):
	def get_sprite(self, game, pos):
		pos = Point(pos)
		cell_info = game.scene.get_cell_info(pos)
		return game.get_cell_repr(pos, cell_info)
	def should_get_visible_surroundings(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_viewport(), Size(20, 10))
		self.assertEqual(self.get_sprite(dungeon, (9, 6)), '@')
		self.assertEqual(self.get_sprite(dungeon, (5, 6)), '.')
		self.assertEqual(self.get_sprite(dungeon, (5, 5)), '#')
		self.assertEqual(self.get_sprite(dungeon, (10, 1)), None)
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(self.get_sprite(dungeon, (9, 6)), '.')
		self.assertEqual(self.get_sprite(dungeon, (5, 6)), None)
		self.assertEqual(self.get_sprite(dungeon, (5, 5)), '#')
		self.assertEqual(self.get_sprite(dungeon, (10, 1)), '>')
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(self.get_sprite(dungeon, (10, 1)), '>')
	def should_get_visible_monsters_and_items(self):
		dungeon = self.dungeon = mock_dungeon.build('monsters on top')
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(self.get_sprite(dungeon, (1, 1)), 'M')
		self.assertEqual(self.get_sprite(dungeon, (1, 6)), 'M')
		self.assertEqual(self.get_sprite(dungeon, (2, 6)), '!')
		dungeon.jump_to(Point(10, 1))
		self.assertEqual(self.get_sprite(dungeon, (1, 1)), None)
		self.assertEqual(self.get_sprite(dungeon, (1, 6)), None)
		self.assertEqual(self.get_sprite(dungeon, (2, 6)), None)
	def should_see_monsters_only_in_the_field_of_vision(self):
		dungeon = self.dungeon = mock_dungeon.build('now you see me')
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
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
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
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
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+   
				_ |@.|   
				_ ^..^   
				_ |.>|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.move(dungeon.get_player(), game.Direction.DOWN)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+   
				_ |..|   
				_ ^.@^   
				_ |.>|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+   
				_ |..|   
				_ ^..@#  
				_ |.>|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+   
				_ |  | # 
				_ ^  ^@# 
				_ | >|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+   
				_ |  | # 
				_ ^  ^#@ 
				_ | >|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+ # 
				_ |  | @ 
				_ ^  ^## 
				_ | >|   
				_ +--+   
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_ +--+ @ 
				_ |  | # 
				_ ^  ^   
				_ | >|   
				_ +--+   
				""").replace('_', ' '))

class TestMovement(AbstractTestDungeon):
	def should_move_player_character(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		dungeon.move(dungeon.get_player(), game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(9, 5))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(10, 5))
		dungeon.move(dungeon.get_player(), game.Direction.DOWN), 
		self.assertEqual(dungeon.get_player().pos, Point(10, 6))
		dungeon.move(dungeon.get_player(), game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		dungeon.move(dungeon.get_player(), game.Direction.UP_LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(8, 5))
		dungeon.move(dungeon.get_player(), game.Direction.DOWN_LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(7, 6))
		dungeon.move(dungeon.get_player(), game.Direction.DOWN_RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(8, 7))
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertEqual(dungeon.tostring(), textwrap.dedent(mock_dungeon._MockBuilderUnSettler.MAP_DATA))
	def should_update_fov_after_movement(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertFalse(dungeon.scene.remembered_exit)
		self.maxDiff = None
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
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
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT) 
		self.assertFalse(dungeon.scene.remembered_exit)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
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
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT) 
		dungeon.move(dungeon.get_player(), game.Direction.UP) 
		dungeon.move(dungeon.get_player(), game.Direction.UP) 
		dungeon.move(dungeon.get_player(), game.Direction.UP) 
		self.assertTrue(dungeon.scene.remembered_exit)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
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
	def should_not_move_player_into_the_void(self):
		dungeon = self.dungeon = mock_dungeon.build('mini lonely')
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		dungeon.move(dungeon.get_player(), game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		dungeon.move(dungeon.get_player(), game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
	def should_not_move_player_into_a_wall(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 2 lonely')
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		dungeon.move(dungeon.get_player(), game.Direction.DOWN), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 1))
	def should_move_player_through_a_wall_in_noclip_mode(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 3 lonely')
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		dungeon.god.noclip = True
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(1, 0))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(2, 0))
	def should_move_player_diagonally_only_if_allowed(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 4 lonely')
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.UP_LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertEqual(dungeon.get_player().pos, Point(2, 2))
	def should_not_allow_move_player_diagonally_in_autoexplore_mode(self):
		dungeon = self.dungeon = mock_dungeon.build('mini rogue 2 lonely')
		list(dungeon.process_events(raw=True)) # Clear events.
		self.assertTrue(dungeon.start_autoexploring())
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(2, 2))
	def should_not_allow_move_player_diagonally_in_autowalk_mode(self):
		dungeon = self.dungeon = mock_dungeon.build('mini rogue 2 lonely')
		list(dungeon.process_events(raw=True)) # Clear events.
		dungeon.walk_to(Point(7, 1))
		self.assertTrue(dungeon.start_autoexploring())
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(2, 2))
	def should_not_allow_move_player_diagonally_both_from_and_to_good_cell(self):
		dungeon = self.dungeon = mock_dungeon.build('mini rogue lonely')
		self.assertEqual(dungeon.get_player().pos, Point(3, 1))

		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.UP))
		self.assertEqual(dungeon.get_player().pos, Point(7, 1))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.LEFT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertEqual(dungeon.get_player().pos, Point(4, 3))
	def should_descend_to_new_map(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 5 lonely')
		dungeon.affect_health(dungeon.get_player(), -5)
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		dungeon.descend()
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		dungeon.move(dungeon.get_player(), game.Direction.DOWN), 
		dungeon.move(dungeon.get_player(), game.Direction.DOWN), 
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		dungeon.descend()
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		self.assertEqual(dungeon.get_player().hp, 5)
		self.assertEqual(dungeon.tostring(), textwrap.dedent(mock_dungeon._MockMiniBuilderUnSettler.MAP_DATA).replace('~', '.'))
	def should_directly_jump_to_new_position(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		dungeon.jump_to(Point(11, 2))
		self.maxDiff = None
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				    #######      #  
				         #>##       
				         #.@#       
				     ##  ##.#       
				     #    ...       
				#    #    ...       
				#        .....     #
				#        .....      
				#       .......     
				 #################  
				"""))

class TestActorEffects(AbstractTestDungeon):
	def should_heal_thyself(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.affect_health(dungeon.get_player(), -1)
		self.assertEqual(dungeon.get_player().hp, 9)
		dungeon.affect_health(dungeon.get_player(), -1)
		self.assertEqual(dungeon.get_player().hp, 8)
		dungeon.affect_health(dungeon.get_player(), +100)
		self.assertEqual(dungeon.get_player().hp, 10)
		dungeon.affect_health(dungeon.get_player(), -100)
		self.assertIsNone(dungeon.get_player())

class TestItemActions(AbstractTestDungeon):
	def should_grab_item(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around')
		list(dungeon.process_events(raw=True))

		dungeon.grab_item_at(dungeon.get_player(), Point(9, 6))
		self.assertEqual(dungeon.events, [])

		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		self.assertEqual(list(map(str, dungeon.events)), [
			'GrabItemEvent(actor=player, item=potion)',
			])

		list(dungeon.process_events(raw=True))
		dungeon.grab_item_at(dungeon.get_player(), Point(11, 6))
		self.assertEqual(list(map(str, dungeon.events)), [
			'GrabItemEvent(actor=player, item=healing potion)',
			])
	def should_consume_item(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around')
		dungeon.affect_health(dungeon.get_player(), -9)
		list(dungeon.process_events(raw=True))
		dungeon.get_player().inventory.append(dungeon.ITEMS['potion']())
		dungeon.get_player().inventory.append(dungeon.ITEMS['healing_potion']())

		dungeon.consume_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'ConsumeItemEvent(actor=player, item=potion)',
			])
		self.assertEqual(len(dungeon.get_player().inventory), 1)
		self.assertEqual(dungeon.get_player().inventory[0].name, 'healing potion')

		list(dungeon.process_events(raw=True))
		dungeon.consume_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'ConsumeItemEvent(actor=player, item=healing potion)',
			'HealthEvent(target=player, diff=5)',
			])
		self.assertEqual(dungeon.get_player().hp, 6)
		self.assertEqual(len(dungeon.get_player().inventory), 0)
	def should_equip_item(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around')
		list(dungeon.process_events(raw=True))
		dungeon.get_player().inventory.append(dungeon.ITEMS['weapon']())
		dungeon.get_player().inventory.append(dungeon.ITEMS['ranged']())

		dungeon.wield_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'EquipItemEvent(actor=player, item=weapon)',
			])
		self.assertEqual(dungeon.get_player().wielding.name, 'weapon')
		self.assertEqual(len(dungeon.get_player().inventory), 1)
		self.assertEqual(dungeon.get_player().inventory[0].name, 'ranged')

		list(dungeon.process_events(raw=True))
		dungeon.wield_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'UnequipItemEvent(actor=player, item=weapon)',
			'EquipItemEvent(actor=player, item=ranged)',
			])
		self.assertEqual(dungeon.get_player().wielding.name, 'ranged')
		self.assertEqual(len(dungeon.get_player().inventory), 1)
		self.assertEqual(dungeon.get_player().inventory[0].name, 'weapon')

		list(dungeon.process_events(raw=True))
		dungeon.unwield_item(dungeon.get_player())
		self.assertEqual(list(map(str, dungeon.events)), [
			'UnequipItemEvent(actor=player, item=ranged)',
			])
		self.assertIsNone(dungeon.get_player().wielding)
		self.assertEqual(len(dungeon.get_player().inventory), 2)
		self.assertEqual(dungeon.get_player().inventory[0].name, 'weapon')
		self.assertEqual(dungeon.get_player().inventory[1].name, 'ranged')

		list(dungeon.process_events(raw=True))
		dungeon.unwield_item(dungeon.get_player())
		self.assertEqual(len(dungeon.events), 0)
		self.assertIsNone(dungeon.get_player().wielding)
		self.assertEqual(len(dungeon.get_player().inventory), 2)

class TestFight(AbstractTestDungeon):
	def should_move_to_attack_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close monster')

		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		self.assertEqual(monster.hp, 2)
	def should_attack_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close monster')
		list(dungeon.process_events(raw=True))
		
		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		dungeon.attack(dungeon.get_player(), monster)
		self.assertEqual(monster.hp, 2)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), game.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, dungeon.get_player())
		self.assertEqual(dungeon.events[0].target, monster)
		self.assertEqual(type(dungeon.events[1]), game.HealthEvent)
		self.assertEqual(dungeon.events[1].target, monster)
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_kill_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close monster')

		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		monster.hp = 1
		dungeon.attack(dungeon.get_player(), monster)
		self.assertEqual(type(dungeon.events[-1]), game.DeathEvent)
		self.assertEqual(dungeon.events[-1].target, monster)
		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		self.assertIsNone(monster)
	def should_drop_loot_from_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close thief')

		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		monster.hp = 1
		dungeon.attack(dungeon.get_player(), monster)

		item = next(dungeon.scene.iter_items_at((10, 6)))
		self.assertEqual(item.name, 'money')
		self.assertEqual(type(dungeon.events[-1]), game.DropItemEvent)
		self.assertEqual(dungeon.events[-1].actor, monster)
		self.assertEqual(dungeon.events[-1].item, item)
	def should_be_attacked_by_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close inert monster')
		list(dungeon.process_events(raw=True))
		
		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.get_player().hp, 9)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), game.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].target, dungeon.get_player())
		self.assertEqual(type(dungeon.events[1]), game.HealthEvent)
		self.assertEqual(dungeon.events[1].target, dungeon.get_player())
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_be_killed_by_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close inert monster')
		dungeon.get_player().hp = 1
		list(dungeon.process_events(raw=True))
		
		monster = next(dungeon.scene.iter_actors_at((10, 6)), None)
		player = dungeon.get_player()
		dungeon.scene.monsters[-1].act(dungeon)
		self.assertIsNone(dungeon.get_player())
		self.assertEqual(len(dungeon.events), 3)
		self.assertEqual(type(dungeon.events[0]), game.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].target, player)
		self.assertEqual(type(dungeon.events[1]), game.HealthEvent)
		self.assertEqual(dungeon.events[1].target, player)
		self.assertEqual(dungeon.events[1].diff, -1)
		self.assertEqual(type(dungeon.events[-1]), game.DeathEvent)
		self.assertEqual(dungeon.events[-1].target, player)
	def should_angry_move_to_attack_player(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster')
		list(dungeon.process_events(raw=True))

		monster = dungeon.scene.monsters[-1]
		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.scene.monsters[-1].pos, Point(10, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), game.MoveEvent)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].dest, Point(10, 6))
		list(dungeon.process_events(raw=True))

		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), game.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].target, dungeon.get_player())
		self.assertEqual(type(dungeon.events[1]), game.HealthEvent)
		self.assertEqual(dungeon.events[1].target, dungeon.get_player())
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_not_angry_move_when_player_is_out_of_sight(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster 2')
		list(dungeon.process_events(raw=True))

		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.scene.monsters[-1].pos, Point(4, 4))
		self.assertEqual(len(dungeon.events), 0)

class TestAutoMode(AbstractTestDungeon):
	def should_auto_walk_to_position(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertFalse(dungeon.perform_automovement())
		dungeon.walk_to(Point(11, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Notices stairs and stops.
		list(dungeon.process_events(raw=True)) # Clear events.
		self.assertFalse(dungeon.perform_automovement())

		dungeon.walk_to(Point(11, 2))
		self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # You have reached your destination.

		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				  #########      ###
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
	def should_not_stop_immediately_in_auto_mode_if_exit_is_already_visible(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 6 lonely')
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		list(dungeon.process_events(raw=True)) # Clear events.

		dungeon.walk_to(Point(1, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(0, 1))
	def should_not_allow_autowalking_if_monsters_are_nearby(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 6 monster')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		list(dungeon.process_events(raw=True)) # Clear events.

		dungeon.walk_to(Point(12, 8))
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), game.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, 'monsters')
	def should_autoexplore(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertFalse(dungeon.perform_automovement())
		self.assertTrue(dungeon.start_autoexploring())
		for _ in range(12):
			self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Notices stairs and stops.
		list(dungeon.process_events(raw=True)) # Clear events.
		self.assertFalse(dungeon.perform_automovement())

		self.assertTrue(dungeon.start_autoexploring())
		for _ in range(5):
			self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Explored everything.

		self.assertFalse(dungeon.start_autoexploring()) # And Jesus wept.

		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				####################
				#        #>##......#
				#        #  #......#
				#    ##  ## #@.....#
				#    #     ........#
				#    #   ..........#
				#      ............#
				#    ..............#
				#    ..............#
				####################
				"""))
	def should_not_allow_autoexploring_if_monsters_are_nearby(self):
		dungeon = self.dungeon = mock_dungeon.build('single mock monster')
		list(dungeon.process_events(raw=True)) # Clear events.

		self.assertFalse(dungeon.start_autoexploring())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), game.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, 'monsters')

class TestGameSerialization(AbstractTestDungeon):
	def should_load_game_or_start_new_one(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		self.assertEqual(dungeon.scene.monsters[0].pos, Point(9, 6))
		dungeon.scene.monsters[0].pos = Point(2, 2)
		writer = savefile.Writer(MockWriterStream(), game.Version.CURRENT)
		dungeon.save(writer)
		dump = writer.f.dump

		reader = savefile.Reader(iter(dump))
		restored_dungeon = MockGame()
		restored_dungeon.load(reader)

		self.assertEqual(restored_dungeon.scene.monsters[0].pos, Point(2, 2))

		restored_dungeon = self.dungeon = mock_dungeon.build('mock settler restored')
		self.assertEqual(restored_dungeon.scene.monsters[0].pos, Point(9, 6))

	def should_serialize_and_deserialize_game(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		writer = savefile.Writer(MockWriterStream(), game.Version.CURRENT)
		dungeon.save(writer)
		dump = writer.f.dump[1:]
		Wall = mock_dungeon.MockGame.TERRAIN['Wall'].__name__
		Floor = mock_dungeon.MockGame.TERRAIN['Floor'].__name__
		self.assertEqual(dump, list(map(str, [1406932606,
			10, 1, 0,
			20, 10,
			Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall, Floor, Wall, Wall, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall, Floor, Floor, Wall, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Wall, Wall, Floor, Floor, Wall, Wall, Floor, Wall, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall,
			20, 10,
			0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0,
			0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0,
			0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0,
			0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
			0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
			1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
			1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
			1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
			1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0,
			0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0,

			2,
				'Player', 9, 6, 10, 0, 0, 0,
				'MockMonster', 2, 5, 3, 0, 0, 0,
			1,
				'Potion', 10, 6,
			])))
		dump = [str(game.Version.CURRENT)] + list(map(str, dump))
		restored_dungeon = MockGame()
		self.assertEqual(game.Version.CURRENT, game.Version.WIELDING + 1)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(
				[(_.name, _.pos) for _ in dungeon.scene.monsters],
				[(_.name, _.pos) for _ in restored_dungeon.scene.monsters],
				)
		self.assertEqual(dungeon.scene.exit_pos, restored_dungeon.scene.exit_pos)
		for pos in dungeon.scene.strata.size.iter_points():
			self.assertEqual(dungeon.scene.strata.cell(pos).sprite, restored_dungeon.scene.strata.cell(pos).sprite, str(pos))
			self.assertEqual(dungeon.scene.strata.cell(pos).passable, restored_dungeon.scene.strata.cell(pos).passable, str(pos))
			self.assertEqual(dungeon.scene.strata.cell(pos).remembered, restored_dungeon.scene.strata.cell(pos).remembered, str(pos))
			self.assertEqual(dungeon.scene.visited.cell(pos), restored_dungeon.scene.visited.cell(pos), str(pos))
		self.assertEqual(len(dungeon.scene.monsters), len(restored_dungeon.scene.monsters))
		for monster, restored_monster in zip(dungeon.scene.monsters, restored_dungeon.scene.monsters):
			self.assertEqual(monster.name, restored_monster.name)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.scene.remembered_exit, restored_dungeon.scene.remembered_exit)
		self.assertEqual(len(dungeon.scene.items), len(restored_dungeon.scene.items))
		for item, restored_item in zip(dungeon.scene.items, restored_dungeon.scene.items):
			self.assertEqual(item.item.name, restored_item.item.name)
			self.assertEqual(item.pos, restored_item.pos)
