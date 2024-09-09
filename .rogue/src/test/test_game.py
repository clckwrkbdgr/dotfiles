import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from ..math import Point, Size
from ..pcg._base import RNG
from ..pcg import builders, settlers
from .. import monsters, items
from .. import pcg
from .. import game
from .. import ui
from .. import messages
from ..system import savefile

class MockWriterStream:
	def __init__(self):
		self.dump = []
	def write(self, item):
		if item == '\0':
			return
		self.dump.append(item)

class MockGame(game.Game):
	SPECIES = {
			'player' : monsters.Species('player', "@", 10, vision=10),
			'monster' : monsters.Species('monster', "M", 3, vision=10),
			'thief' : monsters.Species('thief', "T", 10, vision=10, drops=[
				(1, 'money'),
				]),
			}
	ITEMS = {
			'potion' : items.ItemType('potion', '!', items.Effect.NONE),
			'healing potion' : items.ItemType('healing potion', '!', items.Effect.HEALING),
			'money' : items.ItemType('money', '$', items.Effect.NONE),
			}
	TERRAIN = {
		None : game.Terrain(' ', False),
		'#' : game.Terrain("#", False, remembered='#'),
		'.' : game.Terrain(".", True),
		'~' : game.Terrain(".", True, allow_diagonal=False),
		}

class MockRogueDungeon(MockGame):
	TERRAIN = {
		None : game.Terrain(' ', False),
		' ' : game.Terrain(' ', False),
		'#' : game.Terrain("#", True, remembered='#', allow_diagonal=False, dark=True),
		'.' : game.Terrain(".", True),
		'+' : game.Terrain("+", False, remembered='+'),
		'-' : game.Terrain("-", False, remembered='-'),
		'|' : game.Terrain("|", False, remembered='|'),
		'^' : game.Terrain("^", True, remembered='^', allow_diagonal=False, dark=True),
		}

class MockDarkRogueDungeon(MockGame):
	TERRAIN = {
		None : game.Terrain(' ', False),
		' ' : game.Terrain(' ', False),
		'#' : game.Terrain("#", True, allow_diagonal=False, dark=True),
		'.' : game.Terrain(".", True),
		'+' : game.Terrain("+", False),
		'-' : game.Terrain("-", False),
		'|' : game.Terrain("|", False),
		'^' : game.Terrain("^", True, allow_diagonal=False, dark=True),
		}

class UnSettler(settlers.Settler):
	def _populate(self):
		pass

class CustomSettler(settlers.Settler):
	MONSTERS = [
			]
	ITEMS = [
			]
	def _populate(self):
		self.monsters += self.MONSTERS
	def _place_items(self):
		self.items += self.ITEMS

class SingleMockMonster(settlers.SingleMonster):
	MONSTER = ('monster', monsters.Behavior.ANGRY)

class MockUI(ui.UI):
	def __init__(self, user_actions, interrupts):
		self.events = []
		self.user_actions = list(user_actions)
		self.interrupts = interrupts
	def __enter__(self): # pragma: no cover
		self.events.append('__enter__')
		return self
	def __exit__(self, *targs): # pragma: no cover
		self.events.append('__exit__')
		pass
	def redraw(self, game): # pragma: no cover
		self.events.append('redraw')
	def user_interrupted(self): # pragma: no cover
		self.events.append('user_interrupted')
		return self.interrupts.pop(0)
	def user_action(self, game): # pragma: no cover
		self.events.append('user_action')
		for event in game.events:
			self.events.append(str(event))
		return self.user_actions.pop(0)

class AbstractTestDungeon(unittest.TestCase):
	class _MockBuilder(builders.CustomMap):
		MAP_DATA = """\
			####################
			#........#>##......#
			#........#..#......#
			#....##..##.#......#
			#....#.............#
			#....#.............#
			#........@.........#
			#..................#
			#..................#
			####################
			"""

class TestMainDungeonLoop(AbstractTestDungeon):
	def should_run_main_loop(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
		mock_ui = MockUI(user_actions=[
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
			self.assertTrue(dungeon.main_loop(mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			] + [
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @Point(x=9, y=5) 10/10hp moves to Point(x=9, y=5)',
			'redraw',
			'user_action',
			'player @Point(x=9, y=6) 10/10hp moves to Point(x=9, y=6)',
			'redraw',
			'user_action',
			] + [ # walking...
			'redraw',
			'user_interrupted',
			] * 2 + ['redraw'] + [ # NONE AUTOEXPLORE
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
			] * 3 + ['redraw'] + [ # GOD_TOGGLE_* EXIT
			'redraw',
			'user_action',
			] * 3 + [
			'__exit__',
			])
	def should_perform_monsters_turns_after_player_has_done_with_their_turn(self):
		class _FightingGround(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(10, 6)),
				('monster', settlers.Behavior.INERT, Point(9, 4)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_FightingGround])
		mock_ui = MockUI(user_actions=[
			(ui.Action.NONE, None),
			(ui.Action.MOVE, game.Direction.UP), # Step in.
			(ui.Action.NONE, None),
			(ui.Action.MOVE, game.Direction.UP), # Attack.
			(ui.Action.WAIT, None), # Just wait.
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(dungeon.main_loop(mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'Discovered monster @Point(x=10, y=6) 3/3hp',
			'Discovered monster @Point(x=9, y=4) 3/3hp',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @Point(x=9, y=5) 9/10hp moves to Point(x=9, y=5)',
			'monster @Point(x=9, y=4) 3/3hp attacks player @Point(x=9, y=5) 9/10hp',
			'player @Point(x=9, y=5) 9/10hp -1 hp',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @Point(x=9, y=5) 8/10hp attacks monster @Point(x=9, y=4) 2/3hp',
			'monster @Point(x=9, y=4) 2/3hp -1 hp',
			'monster @Point(x=9, y=4) 2/3hp attacks player @Point(x=9, y=5) 8/10hp',
			'player @Point(x=9, y=5) 8/10hp -1 hp',
			'redraw',
			'user_action',
			'monster @Point(x=9, y=4) 2/3hp attacks player @Point(x=9, y=5) 7/10hp',
			'player @Point(x=9, y=5) 7/10hp -1 hp',
			'__exit__',
			])
		self.assertEqual(dungeon.get_player().hp, 7)
		self.assertEqual(dungeon.monsters[2].hp, 2)
	def should_die_after_monster_attack(self):
		class _FightingGround(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(10, 6)),
				('monster', settlers.Behavior.INERT, Point(9, 4)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_FightingGround])
		mock_ui = MockUI(user_actions=[
			(ui.Action.NONE, None),
			(ui.Action.MOVE, game.Direction.UP), # Step in.
			] + [
			(ui.Action.WAIT, None), # Just wait while monster kills you.
			] * 10, interrupts=[],
		)
		with mock_ui:
			self.assertFalse(dungeon.main_loop(mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'Discovered monster @Point(x=10, y=6) 3/3hp',
			'Discovered monster @Point(x=9, y=4) 3/3hp',
			'redraw',
			'user_action',
			'redraw',
			'user_action',
			'player @Point(x=9, y=5) 9/10hp moves to Point(x=9, y=5)',
			'monster @Point(x=9, y=4) 3/3hp attacks player @Point(x=9, y=5) {0}/10hp'.format(9),
			'player @Point(x=9, y=5) {0}/10hp -1 hp'.format(9),
			] + sum(([
			'redraw',
			'user_action',
			'monster @Point(x=9, y=4) 3/3hp attacks player @Point(x=9, y=5) {0}/10hp'.format(9 - i),
			'player @Point(x=9, y=5) {0}/10hp -1 hp'.format(9 - i),
			] for i in range(1, 9)), []) + [
			'redraw',
			'__exit__',
			])
		self.assertIsNone(dungeon.get_player())
		self.assertEqual(dungeon.monsters[1].hp, 3)
	def should_suicide_out_of_main_loop(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
		mock_ui = MockUI(user_actions=[
			(ui.Action.SUICIDE, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertFalse(dungeon.main_loop(mock_ui))
		self.assertIsNone(dungeon.get_player())
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'redraw',
			'__exit__',
			])
	def should_grab_items(self):
		class _PotionsLyingAround(CustomSettler):
			ITEMS = [
				('potion', Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_PotionsLyingAround])
		mock_ui = MockUI(user_actions=[
			(ui.Action.MOVE, game.Direction.RIGHT),
			(ui.Action.GRAB, Point(10, 6)),
			(ui.Action.EXIT, None),
			], interrupts=[],
		)
		with mock_ui:
			self.assertTrue(dungeon.main_loop(mock_ui))
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'Discovered potion @Point(x=10, y=6)',
			'redraw',
			'user_action',
			'player @Point(x=10, y=6) 10/10hp moves to Point(x=10, y=6)',
			'redraw',
			'user_action',
			'player @Point(x=10, y=6) 10/10hp grabs potion @Point(x=10, y=6)',
			'player @Point(x=10, y=6) 10/10hp consumes potion @Point(x=10, y=6)',
			'__exit__',
			])

class TestEvents(AbstractTestDungeon):
	def should_notify_when_found_exit(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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
		class _NowYouSeeMe(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(1, 1)),
				('monster', settlers.Behavior.DUMMY, Point(1, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_NowYouSeeMe])
		dungeon.jump_to(Point(11, 2))
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(dungeon.events[0].obj, dungeon.monsters[2])
		self.assertEqual(dungeon.events[1].obj, '>')

		dungeon.clear_event(dungeon.events[1])
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, dungeon.monsters[2])
	def should_notify_when_see_monsters(self):
		class _NowYouSeeMe(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(1, 1)),
				('monster', settlers.Behavior.DUMMY, Point(1, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_NowYouSeeMe])
		# At start we see just the one monster.
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, dungeon.monsters[2])
		dungeon.clear_event()

		# Now we see both, but reporting only the new one.
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, dungeon.monsters[1])
		dungeon.clear_event()

		# Now we see just the original one - visibility did not change.
		dungeon.jump_to(Point(9, 6))
		self.assertEqual(dungeon.events, [])

		# Now we see both, but reporting only the new one again.
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(dungeon.events[0].obj, dungeon.monsters[1])
		dungeon.clear_event()

class TestVisibility(AbstractTestDungeon):
	def should_get_visible_surroundings(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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
		class _MonstersOnTopOfItems(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(1, 1)),
				('monster', settlers.Behavior.DUMMY, Point(1, 6)),
				]
			ITEMS = [
				('potion', Point(2, 6)),
				('potion', Point(1, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_MonstersOnTopOfItems])
		dungeon.jump_to(Point(2, 2))
		self.assertEqual(dungeon.get_sprite(1, 1), 'M')
		self.assertEqual(dungeon.get_sprite(1, 6), 'M')
		self.assertEqual(dungeon.get_sprite(2, 6), '!')
		dungeon.jump_to(Point(10, 1))
		self.assertEqual(dungeon.get_sprite(1, 1), None)
		self.assertEqual(dungeon.get_sprite(1, 6), None)
		self.assertEqual(dungeon.get_sprite(2, 6), None)
	def should_see_monsters_only_in_the_field_of_vision(self):
		class _NowYouSeeMe(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(1, 1)),
				('monster', settlers.Behavior.DUMMY, Point(1, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_NowYouSeeMe])
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
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				+--+ #
				|@.| #
				|..^##
				|.>|  
				+--+  
				"""
		dungeon = MockDarkRogueDungeon(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				+--+  
				|@.|  
				|..^  
				|.>|  
				+--+  
				"""))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.move(dungeon.get_player(), game.Direction.DOWN)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				+--+  
				|..|  
				|.@^  
				|.>|  
				+--+  
				"""))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				+--   
				|..|  
				|..@# 
				|.>|  
				+--   
				"""))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_     
				_  | #
				_  ^@#
				_ >|  
				_     
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_     
				_    #
				_   #@
				_ >   
				_     
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_    #
				_    @
				_   ##
				_ >   
				_     
				""").replace('_', ' '))
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_    @
				_    #
				_     
				_ >   
				_     
				""").replace('_', ' '))

class TestMovement(AbstractTestDungeon):
	def should_convert_shift_to_direction(self):
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(0, 0)), None)

		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(1, 0)), game.Direction.RIGHT)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(-1, 0)), game.Direction.LEFT)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(0, 1)), game.Direction.DOWN)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(0, -1)), game.Direction.UP)

		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(-1, 1)), game.Direction.DOWN_LEFT)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(1, -1)), game.Direction.UP_RIGHT)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(-1, -1)), game.Direction.UP_LEFT)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(1, 1)), game.Direction.DOWN_RIGHT)

		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(2, 0)), game.Direction.RIGHT)
		self.assertEqual(game.Game.get_direction(Point(0, 0), Point(2, 3)), game.Direction.DOWN_RIGHT)
	def should_move_player_character(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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

		self.assertEqual(dungeon.tostring(), textwrap.dedent(self._MockBuilder.MAP_DATA))
	def should_update_fov_after_movement(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				@...#
				....#
				...>#
				#####
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		dungeon.move(dungeon.get_player(), game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		dungeon.move(dungeon.get_player(), game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
	def should_not_move_player_into_a_wall(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				#####
				#.@.#
				#..>#
				#####
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.move(dungeon.get_player(), game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		dungeon.move(dungeon.get_player(), game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(1, 1))
	def should_move_player_through_a_wall_in_noclip_mode(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#.@#.#
				#...>#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.god.noclip = True
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(3, 1))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(4, 1))
	def should_move_player_diagonally_only_if_allowed(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#@#~>#
				#~#~##
				#~~~~#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.get_player().pos, Point(1, 1))

		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.UP_LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertEqual(dungeon.get_player().pos, Point(3, 3))
	def should_not_allow_move_player_diagonally_in_autoexplore_mode(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				+--+  
				|.@| #
				|..^##
				|.>|  
				+--+  
				"""
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		dungeon.clear_event() # Clear events.
		self.assertTrue(dungeon.start_autoexploring())
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(2, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
	def should_not_allow_move_player_diagonally_in_autowalk_mode(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				+--+  
				|.@| #
				|..^##
				|.>|  
				+--+  
				"""
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		dungeon.clear_event() # Clear events.
		dungeon.walk_to(Point(5, 1))
		self.assertTrue(dungeon.start_autoexploring())
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(2, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
	def should_not_allow_move_player_diagonally_both_from_and_to_good_cell(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				+--+  
				|@.| #
				|..^##
				|.>|  
				+--+  
				"""
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.get_player().pos, Point(1, 1))

		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.RIGHT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.UP))
		self.assertEqual(dungeon.get_player().pos, Point(5, 1))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.LEFT))
		self.assertFalse(dungeon.move(dungeon.get_player(), game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.LEFT))
		self.assertTrue(dungeon.move(dungeon.get_player(), game.Direction.DOWN))
		self.assertEqual(dungeon.get_player().pos, Point(2, 3))
	def should_descend_to_new_map(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#.@>.#
				#....#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		dungeon.affect_health(dungeon.get_player(), -5)
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.descend()
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT), 
		dungeon.descend()
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		self.assertEqual(dungeon.get_player().hp, 5)
		self.assertEqual(dungeon.tostring(), textwrap.dedent(_MockBuilder.MAP_DATA))
	def should_directly_jump_to_new_position(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
		dungeon.affect_health(dungeon.get_player(), -1)
		self.assertEqual(dungeon.get_player().hp, 9)
		dungeon.affect_health(dungeon.get_player(), -1)
		self.assertEqual(dungeon.get_player().hp, 8)
		dungeon.affect_health(dungeon.get_player(), +100)
		self.assertEqual(dungeon.get_player().hp, 10)
		dungeon.affect_health(dungeon.get_player(), -100)
		self.assertIsNone(dungeon.get_player())

class TestItemActions(AbstractTestDungeon):
	class _PotionsLyingAround(CustomSettler):
		ITEMS = [
			('potion', Point(10, 6)),
			('healing potion', Point(11, 6)),
			]
	def should_grab_item(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._PotionsLyingAround])
		dungeon.affect_health(dungeon.get_player(), -9)
		dungeon.clear_event()

		dungeon.grab_item_at(dungeon.get_player(), Point(9, 6))
		self.assertEqual(dungeon.events, [])

		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @Point(x=9, y=6) 1/10hp grabs potion @Point(x=10, y=6)',
			'player @Point(x=9, y=6) 1/10hp consumes potion @Point(x=10, y=6)',
			])

		dungeon.clear_event()
		dungeon.grab_item_at(dungeon.get_player(), Point(11, 6))
		self.assertEqual(list(map(str, dungeon.events)), [
			'player @Point(x=9, y=6) 6/10hp grabs healing potion @Point(x=11, y=6)',
			'player @Point(x=9, y=6) 6/10hp consumes healing potion @Point(x=11, y=6)',
			'player @Point(x=9, y=6) 6/10hp +5 hp',
			])
		self.assertEqual(dungeon.get_player().hp, 6)

class TestFight(AbstractTestDungeon):
	def should_move_to_attack_monster(self):
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])

		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(dungeon.find_monster(10, 6).hp, 2)
	def should_attack_monster(self):
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])
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
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.DUMMY, Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])

		dungeon.find_monster(10, 6).hp = 1
		monster = dungeon.find_monster(10, 6)
		dungeon.attack(dungeon.get_player(), dungeon.find_monster(10, 6))
		self.assertEqual(type(dungeon.events[-1]), messages.DeathEvent)
		self.assertEqual(dungeon.events[-1].target, monster)
		self.assertIsNone(dungeon.find_monster(10, 6))
	def should_drop_loot_from_monster(self):
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('thief', settlers.Behavior.DUMMY, Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])

		dungeon.find_monster(10, 6).hp = 1
		monster = dungeon.find_monster(10, 6)
		dungeon.attack(dungeon.get_player(), dungeon.find_monster(10, 6))

		item = dungeon.find_item(10, 6)
		self.assertEqual(item.item_type.name, 'money')
		self.assertEqual(type(dungeon.events[-1]), messages.DropItemEvent)
		self.assertEqual(dungeon.events[-1].actor, monster)
		self.assertEqual(dungeon.events[-1].item, item)
	def should_be_attacked_by_monster(self):
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.INERT, Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])
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
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.INERT, Point(10, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])
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
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.ANGRY, Point(11, 6)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])
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
		class _CloseMonster(CustomSettler):
			MONSTERS = [
				('monster', settlers.Behavior.ANGRY, Point(4, 4)),
				]
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])
		dungeon.clear_event()

		dungeon._perform_monster_actions(dungeon.monsters[-1])
		self.assertEqual(dungeon.monsters[-1].pos, Point(4, 4))
		self.assertEqual(len(dungeon.events), 0)

class TestAutoMode(AbstractTestDungeon):
	def should_auto_walk_to_position(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#.@..#
				#...>#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[UnSettler])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		dungeon.clear_event() # Clear events.

		dungeon.walk_to(Point(4, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
	def should_not_allow_autowalking_if_monsters_are_nearby(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#.@..#
				#...>#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[SingleMockMonster])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		dungeon.clear_event() # Clear events.

		dungeon.walk_to(Point(4, 2))
		self.assertFalse(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, 'monsters')
	def should_autoexplore(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
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
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[SingleMockMonster])
		dungeon.clear_event() # Clear events.

		self.assertFalse(dungeon.start_autoexploring())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), messages.DiscoverEvent)
		self.assertEqual(dungeon.events[0].obj, 'monsters')

class TestTerrainSavefile(unittest.TestCase):
	def setUp(self):
		self.TERRAIN = {
				'name' : game.Terrain('.'),
				}
		self.TERRAIN['name'].name = 'name'
	def should_load_terrain(self):
		stream = StringIO('666\x00name\x001')
		reader = savefile.Reader(stream)
		reader.set_meta_info('TERRAIN', self.TERRAIN)
		cell = reader.read(game.Cell)
		self.assertEqual(cell.terrain, self.TERRAIN['name'])
		self.assertEqual(cell.visited, True)
	def should_save_terrain(self):
		stream = StringIO()
		writer = savefile.Writer(stream, 666)
		cell = game.Cell(self.TERRAIN['name'])
		cell.visited = True
		writer.write(cell)
		self.assertEqual(stream.getvalue(), '666\x00name\x001')

class TestGameSerialization(AbstractTestDungeon):
	class _MockSettler(CustomSettler):
		MONSTERS = [
				('monster', settlers.Behavior.ANGRY, Point(2, 5)),
				]
		ITEMS = [
				('potion', Point(10, 6)),
				]

	def should_load_game_or_start_new_one(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
		self.assertEqual(dungeon.monsters[0].pos, Point(9, 6))
		dungeon.monsters[0].pos = Point(2, 2)
		writer = savefile.Writer(MockWriterStream(), game.Version.CURRENT)
		dungeon.save(writer)
		dump = writer.f.dump

		reader = savefile.Reader(iter(dump))
		restored_dungeon = MockGame(load_from_reader=reader)
		self.assertEqual(restored_dungeon.monsters[0].pos, Point(2, 2))

		restored_dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler], load_from_reader=None)
		self.assertEqual(restored_dungeon.monsters[0].pos, Point(9, 6))

	def should_deserialize_game_before_terrain_types(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
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
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.sprite, restored_dungeon.strata.cell(pos.x, pos.y).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.passable, restored_dungeon.strata.cell(pos.x, pos.y).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.remembered, restored_dungeon.strata.cell(pos.x, pos.y).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_monsters(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
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
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.sprite, restored_dungeon.strata.cell(pos.x, pos.y).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.passable, restored_dungeon.strata.cell(pos.x, pos.y).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.remembered, restored_dungeon.strata.cell(pos.x, pos.y).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_behavior(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
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
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.sprite, restored_dungeon.strata.cell(pos.x, pos.y).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.passable, restored_dungeon.strata.cell(pos.x, pos.y).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.remembered, restored_dungeon.strata.cell(pos.x, pos.y).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(len(dungeon.monsters), len(restored_dungeon.monsters))
		for monster, restored_monster in zip(dungeon.monsters, restored_dungeon.monsters):
			self.assertEqual(monster.species, restored_monster.species)
			self.assertEqual(monster.behavior, restored_monster.behavior)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_items(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
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
				'monster', 3, 2, 5, 3, 
			]
		dump = [str(game.Version.ITEMS), str(dungeon.rng.seed)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(dungeon.monsters, restored_dungeon.monsters)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.sprite, restored_dungeon.strata.cell(pos.x, pos.y).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.passable, restored_dungeon.strata.cell(pos.x, pos.y).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.remembered, restored_dungeon.strata.cell(pos.x, pos.y).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(len(dungeon.monsters), len(restored_dungeon.monsters))
		for monster, restored_monster in zip(dungeon.monsters, restored_dungeon.monsters):
			self.assertEqual(monster.species, restored_monster.species)
			self.assertEqual(monster.behavior, restored_monster.behavior)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
		self.assertEqual(len(restored_dungeon.items), 0)
	def should_serialize_and_deserialize_game(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
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
				'player', 0, 9, 6, 10, 
				'monster', 3, 2, 5, 3, 
			1,
				'potion', 10, 6,
			])))
		dump = [str(game.Version.CURRENT)] + list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		self.assertEqual(game.Version.CURRENT, game.Version.ITEMS + 1)
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(dungeon.monsters, restored_dungeon.monsters)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.sprite, restored_dungeon.strata.cell(pos.x, pos.y).terrain.sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.passable, restored_dungeon.strata.cell(pos.x, pos.y).terrain.passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).terrain.remembered, restored_dungeon.strata.cell(pos.x, pos.y).terrain.remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(len(dungeon.monsters), len(restored_dungeon.monsters))
		for monster, restored_monster in zip(dungeon.monsters, restored_dungeon.monsters):
			self.assertEqual(monster.species, restored_monster.species)
			self.assertEqual(monster.behavior, restored_monster.behavior)
			self.assertEqual(monster.pos, restored_monster.pos)
			self.assertEqual(monster.hp, restored_monster.hp)
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
		self.assertEqual(len(dungeon.items), len(restored_dungeon.items))
		for item, restored_item in zip(dungeon.items, restored_dungeon.items):
			self.assertEqual(item.item_type, restored_item.item_type)
			self.assertEqual(item.pos, restored_item.pos)
