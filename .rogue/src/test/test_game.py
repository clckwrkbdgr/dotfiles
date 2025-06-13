import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point, Size
from clckwrkbdgr.pcg import RNG
import clckwrkbdgr.tui
from ..pcg import builders
from .. import monsters, items, terrain
from .. import pcg
from .. import game
from .. import ui
from .. import messages
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

class MockUI(clckwrkbdgr.tui.ModeLoop):
	def __init__(self, game, user_actions, interrupts):
		super(MockUI, self).__init__(ui=None)
		self.game = game
		self.events = []
		self.user_actions = list(user_actions)
		self.interrupts = interrupts
	def __enter__(self): # pragma: no cover
		self.events.append('__enter__')
		return self
	def __exit__(self, *targs): # pragma: no cover
		self.events.append('__exit__')
		pass
	def redraw(self): # pragma: no cover
		self.events.append('redraw')
	def _user_action(self): # pragma: no cover
		if self.game.in_automovement():
			self.events.append('user_interrupted')
			if self.interrupts.pop(0):
				return ui.Action.AUTOSTOP, None
			else:
				return ui.Action.NONE, None
		control = self.user_actions.pop(0)
		self.events.append('user_action')
		for event in self.game.events:
			self.events.append(str(event))
		return control
	def action(self):
		if not self.game._pre_action():
			self.modes = [] # Emulate ending loop.
			return False
		action, action_data = self._user_action()
		result = self.game._perform_actors_actions(action, action_data)
		if not result:
			self.modes = [] # Emulate ending loop.
		return result

class AbstractTestDungeon(unittest.TestCase):
	def _formatMessage(self, msg, standardMsg): # pragma: no cover
		if hasattr(self, 'dungeon'):
			msg = (msg or '') + '\n' + self.dungeon.tostring()
		return super(AbstractTestDungeon, self)._formatMessage(msg, standardMsg)
	def main_loop(self, dungeon, loop):
		from ..ui import MainGame
		loop.run(MainGame(dungeon))
		return dungeon.needs_saving()

class TestMainDungeonLoop(AbstractTestDungeon):
	def should_run_main_loop(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.MOVE, game.Direction.UP),
			(ui.Action.MOVE, game.Direction.DOWN),
			(ui.Action.DESCEND, None),
			(ui.Action.WALK_TO, Point(11, 2)),
			(ui.Action.NONE, None),
			(ui.Action.AUTOEXPLORE, None),
			(ui.Action.AUTOEXPLORE, None),
			(ui.Action.GOD_TOGGLE_VISION, None),
			(ui.Action.GOD_TOGGLE_NOCLIP, None),
			(ui.Action.EXIT, None),
			], interrupts=[False] * 2 + [False] * 8 + [True] + [False] * 6,
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			] + [
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 5] 10/10hp moves to [9, 5]',
			'redraw',
			'user_action',
			'player @[9, 6] 10/10hp moves to [9, 6]',
			'redraw',
			'user_action',
			] + [ # walking...
			'redraw',
			'user_interrupted',
			] * 2 + [ # NONE AUTOEXPLORE
			'redraw',
			'user_action',
			] + ['Discovered >'] + [ # exploring...
			'redraw',
			'user_action',
			] + [ # exploring...
			'redraw',
			'user_interrupted',
			] * 9 + ['redraw', 'user_action'] + [
			'redraw',
			'user_interrupted',
			] * 3 + [ # GOD_TOGGLE_* EXIT
			'redraw',
			'user_action',
			] * 3 + [
			'__exit__',
			])
	def should_perform_monsters_turns_after_player_has_done_with_their_turn(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.NONE, None),
			(ui.Action.MOVE, game.Direction.UP), # Step in.
			(ui.Action.NONE, None),
			(ui.Action.MOVE, game.Direction.UP), # Attack.
			(ui.Action.WAIT, None), # Just wait.
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'Discovered monster @[10, 6] 3/3hp',
			'Discovered monster @[9, 4] 3/3hp',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 5] 9/10hp moves to [9, 5]',
			'monster @[9, 4] 3/3hp attacks player @[9, 5] 9/10hp',
			'player @[9, 5] 9/10hp -1 hp',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 5] 8/10hp attacks monster @[9, 4] 2/3hp',
			'monster @[9, 4] 2/3hp -1 hp',
			'monster @[9, 4] 2/3hp attacks player @[9, 5] 8/10hp',
			'player @[9, 5] 8/10hp -1 hp',
			'redraw',
			'user_action',
			'monster @[9, 4] 2/3hp attacks player @[9, 5] 7/10hp',
			'player @[9, 5] 7/10hp -1 hp',
			'__exit__',
			])
		self.assertEqual(dungeon.get_player().hp, 7)
		self.assertEqual(dungeon.monsters[2].hp, 2)
	def should_die_after_monster_attack(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.NONE, None),
			(ui.Action.MOVE, game.Direction.UP), # Step in.
			] + [
			(ui.Action.WAIT, None), # Just wait while monster kills you.
			] * 10, interrupts=[],
		)
		with mock_ui:
			self.assertFalse(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'Discovered monster @[10, 6] 3/3hp',
			'Discovered monster @[9, 4] 3/3hp',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 5] 9/10hp moves to [9, 5]',
			'monster @[9, 4] 3/3hp attacks player @[9, 5] {0}/10hp'.format(9),
			'player @[9, 5] {0}/10hp -1 hp'.format(9),
			] + sum(([
			'redraw',
			'user_action',
			'monster @[9, 4] 3/3hp attacks player @[9, 5] {0}/10hp'.format(9 - i),
			'player @[9, 5] {0}/10hp -1 hp'.format(9 - i),
			] for i in range(1, 9)), []) + [
			'redraw',
			'__exit__',
			])
		self.assertIsNone(dungeon.get_player())
		self.assertEqual(dungeon.monsters[1].hp, 3)
	def should_suicide_out_of_main_loop(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.SUICIDE, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertFalse(self.main_loop(dungeon, mock_ui))
		self.assertIsNone(dungeon.get_player())
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'redraw',
			'__exit__',
			])

class TestItems(AbstractTestDungeon):
	def should_grab_items(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around 2')
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.MOVE, game.Direction.RIGHT),
			(ui.Action.GRAB, Point(10, 6)),
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'Discovered potion @[10, 6]',
			'Discovered healing potion @[11, 6]',
			'redraw',
			'user_action',
			'player @[10, 6] 10/10hp moves to [10, 6]',
			'redraw',
			'user_action',
			'player @[10, 6] 10/10hp grabs potion @[10, 6]',
			'__exit__',
			])
	def should_consume_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['potion'], Point(0, 0)))
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.CONSUME, dungeon.get_player().inventory[0]),
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 6] 10/10hp consumes potion @[0, 0]',
			'__exit__',
			])
	def should_drop_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['potion'], Point(0, 0)))
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.DROP, dungeon.get_player().inventory[0]),
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 6] 10/10hp drops potion @[9, 6]',
			'__exit__',
			])
	def should_equip_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['weapon'], Point(0, 0)))
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.WIELD, dungeon.get_player().inventory[0]),
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 6] 10/10hp equips weapon @[0, 0]',
			'__exit__',
			])
	def should_unequip_items(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		dungeon.get_player().wielding = items.Item(dungeon.ITEMS['weapon'], Point(0, 0))
		mock_ui = MockUI(dungeon, user_actions=[
			(ui.Action.UNWIELD, None),
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(self.main_loop(dungeon, mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @[9, 6] 10/10hp unequips weapon @[0, 0]',
			'__exit__',
			])

class TestEvents(AbstractTestDungeon):
	def should_notify_when_found_exit(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.events, [])
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, '>')
		dungeon.clear_event()
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(dungeon.events, [])
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(dungeon.events, [])
	def should_clear_specific_event_only(self):
		dungeon = self.dungeon = mock_dungeon.build('now you see me')
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.monsters if monster.pos == Point(1, 6)))
		self.assertEqual(dungeon.events[1].obj, '>')

		dungeon.clear_event(dungeon.events[1])
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.monsters if monster.pos == Point(1, 6)))
	def should_notify_when_see_monsters(self):
		dungeon = self.dungeon = mock_dungeon.build('now you see me')
		# At start we see just the one monster.
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.monsters if monster.pos == Point(1, 6)))
		dungeon.clear_event()

		# Now we see both, but reporting only the new one.
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.monsters if monster.pos == Point(1, 1)))
		dungeon.clear_event()

		# Now we see just the original one - visibility did not change.
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(dungeon.events, [])

		# Now we see both, but reporting only the new one again.
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, next(monster for monster in dungeon.monsters if monster.pos == Point(1, 1)))
		dungeon.clear_event()

class TestVisibility(AbstractTestDungeon):
	def should_get_visible_surroundings(self):
		dungeon = self.dungeon = mock_dungeon.build('lonely')
		self.assertEqual(dungeon.get_viewport(), Size(20, 10))
		self.assertEqual(dungeon.get_sprite(9, 6), '@')
		self.assertEqual(dungeon.get_sprite(5, 6), '.')
		self.assertEqual(dungeon.get_sprite(5, 5), '#')
		self.assertEqual(dungeon.get_sprite(10, 1), None)
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(dungeon.get_sprite(9, 6), '.')
		self.assertEqual(dungeon.get_sprite(5, 6), None)
		self.assertEqual(dungeon.get_sprite(5, 5), '#')
		self.assertEqual(dungeon.get_sprite(10, 1), '>')
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(dungeon.get_sprite(10, 1), '>')
	def should_get_visible_monsters_and_items(self):
		dungeon = self.dungeon = mock_dungeon.build('monsters on top')
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(dungeon.get_sprite(1, 1), 'M')
		self.assertEqual(dungeon.get_sprite(1, 6), 'M')
		self.assertEqual(dungeon.get_sprite(2, 6), '!')
		dungeon.jump_to(Point(10, 1))
		self.assertEqual(dungeon.get_sprite(1, 1), None)
		self.assertEqual(dungeon.get_sprite(1, 6), None)
		self.assertEqual(dungeon.get_sprite(2, 6), None)
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

		self.assertFalse(dungeon.remembered_exit)
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
		self.assertFalse(dungeon.remembered_exit)
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
		self.assertTrue(dungeon.remembered_exit)
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
		dungeon.clear_event() # Clear events.
		self.assertTrue(dungeon.start_autoexploring())
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(2, 2))
	def should_not_allow_move_player_diagonally_in_autowalk_mode(self):
		dungeon = self.dungeon = mock_dungeon.build('mini rogue 2 lonely')
		dungeon.clear_event() # Clear events.
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
		dungeon.clear_event()

		dungeon.grab_item_at(dungeon.get_player(), Point(9, 6))
		self.assertEqual(dungeon.events, [])

		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 10/10hp grabs potion @[10, 6]',
			])

		dungeon.clear_event()
		dungeon.grab_item_at(dungeon.get_player(), Point(11, 6))
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 10/10hp grabs healing potion @[11, 6]',
			])
	def should_consume_item(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around')
		dungeon.affect_health(dungeon.get_player(), -9)
		dungeon.clear_event()
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['potion'], Point(0, 0)))
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['healing_potion'], Point(0, 0)))

		dungeon.consume_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 1/10hp consumes potion @[0, 0]',
			])
		self.assertEqual(len(dungeon.get_player().inventory), 1)
		self.assertEqual(dungeon.get_player().inventory[0].item_type.name, 'healing potion')

		dungeon.clear_event()
		dungeon.consume_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 6/10hp consumes healing potion @[0, 0]',
			'player @[9, 6] 6/10hp +5 hp',
			])
		self.assertEqual(dungeon.get_player().hp, 6)
		self.assertEqual(len(dungeon.get_player().inventory), 0)
	def should_equip_item(self):
		dungeon = self.dungeon = mock_dungeon.build('potions lying around')
		dungeon.clear_event()
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['weapon'], Point(0, 0)))
		dungeon.get_player().inventory.append(items.Item(dungeon.ITEMS['ranged'], Point(0, 0)))

		dungeon.wield_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 10/10hp equips weapon @[0, 0]',
			])
		self.assertEqual(dungeon.get_player().wielding.item_type.name, 'weapon')
		self.assertEqual(len(dungeon.get_player().inventory), 1)
		self.assertEqual(dungeon.get_player().inventory[0].item_type.name, 'ranged')

		dungeon.clear_event()
		dungeon.wield_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 10/10hp unequips weapon @[0, 0]',
			'player @[9, 6] 10/10hp equips ranged @[0, 0]',
			])
		self.assertEqual(dungeon.get_player().wielding.item_type.name, 'ranged')
		self.assertEqual(len(dungeon.get_player().inventory), 1)
		self.assertEqual(dungeon.get_player().inventory[0].item_type.name, 'weapon')

		dungeon.clear_event()
		dungeon.unwield_item(dungeon.get_player())
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @[9, 6] 10/10hp unequips ranged @[0, 0]',
			])
		self.assertIsNone(dungeon.get_player().wielding)
		self.assertEqual(len(dungeon.get_player().inventory), 2)
		self.assertEqual(dungeon.get_player().inventory[0].item_type.name, 'weapon')
		self.assertEqual(dungeon.get_player().inventory[1].item_type.name, 'ranged')

		dungeon.clear_event()
		dungeon.unwield_item(dungeon.get_player())
		self.assertEqual(len(dungeon.events), 0)
		self.assertIsNone(dungeon.get_player().wielding)
		self.assertEqual(len(dungeon.get_player().inventory), 2)

class TestFight(AbstractTestDungeon):
	def should_move_to_attack_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close monster')

		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(dungeon.find_monster(10, 6).hp, 2)
	def should_attack_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close monster')
		dungeon.clear_event()
		
		dungeon.attack(dungeon.get_player(), dungeon.find_monster(10, 6))
		self.assertEqual(dungeon.find_monster(10, 6).hp, 2)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), messages.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, dungeon.get_player())
		self.assertEqual(dungeon.events[0].target, dungeon.find_monster(10, 6))
		self.assertEqual(type(dungeon.events[1]), messages.HealthEvent)
		self.assertEqual(dungeon.events[1].target, dungeon.find_monster(10, 6))
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_kill_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close monster')

		dungeon.find_monster(10, 6).hp = 1
		monster = dungeon.find_monster(10, 6)
		dungeon.attack(dungeon.get_player(), dungeon.find_monster(10, 6))
		self.assertEqual(type(dungeon.events[-1]), messages.DeathEvent)
		self.assertEqual(dungeon.events[-1].target, monster)
		self.assertIsNone(dungeon.find_monster(10, 6))
	def should_drop_loot_from_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close thief')

		dungeon.find_monster(10, 6).hp = 1
		monster = dungeon.find_monster(10, 6)
		dungeon.attack(dungeon.get_player(), dungeon.find_monster(10, 6))

		item = dungeon.find_item(10, 6)
		self.assertEqual(item.item_type.name, 'money')
		self.assertEqual(type(dungeon.events[-1]), messages.DropItemEvent)
		self.assertEqual(dungeon.events[-1].actor, monster)
		self.assertEqual(dungeon.events[-1].item, item)
	def should_be_attacked_by_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close inert monster')
		dungeon.clear_event()
		
		dungeon._perform_monster_actions(dungeon.monsters[-1])
		self.assertEqual(dungeon.get_player().hp, 9)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), messages.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, dungeon.find_monster(10, 6))
		self.assertEqual(dungeon.events[0].target, dungeon.get_player())
		self.assertEqual(type(dungeon.events[1]), messages.HealthEvent)
		self.assertEqual(dungeon.events[1].target, dungeon.get_player())
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_be_killed_by_monster(self):
		dungeon = self.dungeon = mock_dungeon.build('close inert monster')
		dungeon.get_player().hp = 1
		dungeon.clear_event()
		
		player = dungeon.get_player()
		dungeon._perform_monster_actions(dungeon.monsters[-1])
		self.assertIsNone(dungeon.get_player())
		self.assertEqual(len(dungeon.events), 3)
		self.assertEqual(type(dungeon.events[0]), messages.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, dungeon.find_monster(10, 6))
		self.assertEqual(dungeon.events[0].target, player)
		self.assertEqual(type(dungeon.events[1]), messages.HealthEvent)
		self.assertEqual(dungeon.events[1].target, player)
		self.assertEqual(dungeon.events[1].diff, -1)
		self.assertEqual(type(dungeon.events[-1]), messages.DeathEvent)
		self.assertEqual(dungeon.events[-1].target, player)
	def should_angry_move_to_attack_player(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster')
		dungeon.clear_event()

		dungeon._perform_monster_actions(dungeon.monsters[-1])
		self.assertEqual(dungeon.monsters[-1].pos, Point(10, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.MoveEvent)
		self.assertEqual(dungeon.events[0].actor, dungeon.find_monster(10, 6))
		self.assertEqual(dungeon.events[0].dest, Point(10, 6))
		dungeon.clear_event()

		dungeon._perform_monster_actions(dungeon.monsters[-1])
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), messages.AttackEvent)
		self.assertEqual(dungeon.events[0].actor, dungeon.find_monster(10, 6))
		self.assertEqual(dungeon.events[0].target, dungeon.get_player())
		self.assertEqual(type(dungeon.events[1]), messages.HealthEvent)
		self.assertEqual(dungeon.events[1].target, dungeon.get_player())
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_not_angry_move_when_player_is_out_of_sight(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster 2')
		dungeon.clear_event()

		dungeon._perform_monster_actions(dungeon.monsters[-1])
		self.assertEqual(dungeon.monsters[-1].pos, Point(4, 4))
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
		dungeon.clear_event() # Clear events.
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
		dungeon.clear_event() # Clear events.

		dungeon.walk_to(Point(1, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(0, 1))
	def should_not_allow_autowalking_if_monsters_are_nearby(self):
		dungeon = self.dungeon = mock_dungeon.build('mini 6 monster')
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		dungeon.clear_event() # Clear events.

		dungeon.walk_to(Point(12, 8))
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
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
		dungeon.clear_event() # Clear events.
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
		dungeon.clear_event() # Clear events.

		self.assertFalse(dungeon.start_autoexploring())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, 'monsters')

class TestGameSerialization(AbstractTestDungeon):
	def should_load_game_or_start_new_one(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		self.assertEqual(dungeon.monsters[0].pos, Point(9, 6))
		dungeon.monsters[0].pos = Point(2, 2)
		writer = savefile.Writer(MockWriterStream(), game.Version.CURRENT)
		dungeon.save(writer)
		dump = writer.f.dump

		reader = savefile.Reader(iter(dump))
		restored_dungeon = MockGame(load_from_reader=reader)
		self.assertEqual(restored_dungeon.monsters[0].pos, Point(2, 2))

		restored_dungeon = self.dungeon = mock_dungeon.build('mock settler restored', load_from_reader=None)
		self.assertEqual(restored_dungeon.monsters[0].pos, Point(9, 6))

	def should_deserialize_game_before_terrain_types(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		dump = [
			9, 6, 10, 1, 0, 20, 10,
			'#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',1, '#',0,'#',0, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0, '.',1,None,0, '#',0,'#',0, '#',0,'#',1, '.',1,None,0, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,0, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0, '.',1,None,0, '.',1,None,1, '#',0,'#',1, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '#',0,'#',1, '#',0,'#',1, '.',1,None,1, '.',1,None,1, '#',0,'#',1, '#',0,'#',1, '.',1,None,1, '#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',1,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',0, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',0, '#',0,'#',0,
			]
		dump = [str(game.Version.TERRAIN_TYPES), str(dungeon.rng.seed)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(dungeon.get_player().pos, restored_dungeon.get_player().pos)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size.iter_points():
			self.assertEqual(dungeon.strata.cell(pos).terrain.sprite, restored_dungeon.strata.cell(pos).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.passable, restored_dungeon.strata.cell(pos).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.remembered, restored_dungeon.strata.cell(pos).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).visited, restored_dungeon.strata.cell(pos).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_monsters(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		dump = [
			9, 6, 10, 1, 0, 20, 10,
			'#',0, '#',0, '#',0, '#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',1, '#',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '.',1, '#',0, '.',0, '#',0, '#',1, '.',0, '.',0, '.',1, '.',1, '.',1, '.',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '#',0, '.',0, '.',1, '#',1, '.',0, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '#',1, '.',1, '.',1, '#',1, '#',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',1,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0,
			]
		dump = [str(game.Version.MONSTERS), str(dungeon.rng.seed)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(dungeon.get_player().pos, restored_dungeon.get_player().pos)
		self.assertEqual(restored_dungeon.get_player().hp, 10)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size.iter_points():
			self.assertEqual(dungeon.strata.cell(pos).terrain.sprite, restored_dungeon.strata.cell(pos).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.passable, restored_dungeon.strata.cell(pos).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.remembered, restored_dungeon.strata.cell(pos).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).visited, restored_dungeon.strata.cell(pos).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_behavior(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		dump = [
			10, 1, 0, 20, 10,
			'#',0, '#',0, '#',0, '#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',1, '#',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '.',1, '#',0, '.',0, '#',0, '#',1, '.',0, '.',0, '.',1, '.',1, '.',1, '.',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '#',0, '.',0, '.',1, '#',1, '.',0, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '#',1, '.',1, '.',1, '#',1, '#',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',1,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0,
			2,
				'player', 9, 6, 10, 
				'monster', 2, 5, 3, 
			]
		dump = [str(game.Version.MONSTER_BEHAVIOR), str(dungeon.rng.seed)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size.iter_points():
			self.assertEqual(dungeon.strata.cell(pos).terrain.sprite, restored_dungeon.strata.cell(pos).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.passable, restored_dungeon.strata.cell(pos).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.remembered, restored_dungeon.strata.cell(pos).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).visited, restored_dungeon.strata.cell(pos).visited, str(pos))
		self.assertEqual(len(dungeon.monsters), len(restored_dungeon.monsters))
		for monster, restored_monster in zip(dungeon.monsters, restored_dungeon.monsters):
			self.assertEqual(monster.species.name, restored_monster.species.name)
			self.assertEqual(monster.behavior, restored_monster.behavior)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_items(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		dump = [
			10, 1, 0, 20, 10,
			'#',0, '#',0, '#',0, '#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',1, '#',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '.',1, '#',0, '.',0, '#',0, '#',1, '.',0, '.',0, '.',1, '.',1, '.',1, '.',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '#',0, '.',0, '.',1, '#',1, '.',0, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '#',1, '.',1, '.',1, '#',1, '#',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',1,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0,
			2,
				'player', 0, 9, 6, 10, 
				'monster', 1, 2, 5, 3, 
			]
		dump = [str(game.Version.ITEMS), str(dungeon.rng.seed)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(
				[(_.species.name, _.pos) for _ in dungeon.monsters],
				[(_.species.name, _.pos) for _ in restored_dungeon.monsters],
				)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size.iter_points():
			self.assertEqual(dungeon.strata.cell(pos).terrain.sprite, restored_dungeon.strata.cell(pos).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.passable, restored_dungeon.strata.cell(pos).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.remembered, restored_dungeon.strata.cell(pos).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).visited, restored_dungeon.strata.cell(pos).visited, str(pos))
		self.assertEqual(len(dungeon.monsters), len(restored_dungeon.monsters))
		for monster, restored_monster in zip(dungeon.monsters, restored_dungeon.monsters):
			self.assertEqual(monster.species.name, restored_monster.species.name)
			self.assertEqual(monster.behavior, restored_monster.behavior)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
		self.assertEqual(len(restored_dungeon.items), 0)
	def should_serialize_and_deserialize_game(self):
		dungeon = self.dungeon = mock_dungeon.build('mock settler')
		writer = savefile.Writer(MockWriterStream(), game.Version.CURRENT)
		dungeon.save(writer)
		dump = writer.f.dump[1:]
		self.assertEqual(dump, list(map(str, [1406932606,
			10, 1, 0, 20, 10,
			'#',0, '#',0, '#',0, '#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',0, '#',1, '#',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '.',1, '#',0, '.',0, '#',0, '#',1, '.',0, '.',0, '.',1, '.',1, '.',1, '.',0, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '.',0, '.',1, '.',1, '.',1, '#',0, '.',0, '.',1, '#',1, '.',0, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '#',1, '.',1, '.',1, '#',1, '#',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '.',0, '.',0, '.',0, '.',0, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',1,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '.',1, '#',0,
			'#',0, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',1, '#',0, '#',0,
			2,
				'player', 0, 9, 6, 10, 0, 0,
				'monster', 1, 2, 5, 3, 0, 0,
			1,
				'potion', 10, 6,
			])))
		dump = [str(game.Version.CURRENT)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		self.assertEqual(game.Version.CURRENT, game.Version.WIELDING + 1)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(
				[(_.species.name, _.pos) for _ in dungeon.monsters],
				[(_.species.name, _.pos) for _ in restored_dungeon.monsters],
				)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size.iter_points():
			self.assertEqual(dungeon.strata.cell(pos).terrain.sprite, restored_dungeon.strata.cell(pos).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.passable, restored_dungeon.strata.cell(pos).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).terrain.remembered, restored_dungeon.strata.cell(pos).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos).visited, restored_dungeon.strata.cell(pos).visited, str(pos))
		self.assertEqual(len(dungeon.monsters), len(restored_dungeon.monsters))
		for monster, restored_monster in zip(dungeon.monsters, restored_dungeon.monsters):
			self.assertEqual(monster.species.name, restored_monster.species.name)
			self.assertEqual(monster.behavior, restored_monster.behavior)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
		self.assertEqual(len(dungeon.items), len(restored_dungeon.items))
		for item, restored_item in zip(dungeon.items, restored_dungeon.items):
			self.assertEqual(item.item_type.name, restored_item.item_type.name)
			self.assertEqual(item.pos, restored_item.pos)
