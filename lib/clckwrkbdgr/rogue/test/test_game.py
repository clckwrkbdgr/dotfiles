import os, sys
import tempfile
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
import textwrap
from ..math import Point, Size
from ..pcg._base import RNG
from ..pcg import builders
from .. import pcg
from .. import game
from .. import ui

BUILTIN_OPEN = 'builtins.open' if sys.version_info[0] >= 3 else '__builtin__.open'

class MockGame(game.Game):
	TERRAIN = {
		None : game.Terrain(' ', False),
		'#' : game.Terrain("#", False, remembered='#'),
		'.' : game.Terrain(".", True),
		'~' : game.Terrain(".", True, allow_diagonal=False),
		}

class MockRogueDungeon(game.Game):
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

class MockDarkRogueDungeon(game.Game):
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
		return self.user_actions.pop(0)

class TestDungeon(unittest.TestCase):
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
	def should_create_new_dungeon(self):
		dungeon = game.Game(rng_seed=123)
		self.assertEqual(dungeon.get_player().pos, Point(17, 21))
		self.assertEqual(dungeon.exit_pos, Point(34, 21))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				################################################################################
				#..............................................................................#
				#..............................................................................#
				#..............................................................................#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############..........................#############...#
				#.......................#############..........................#############...#
				#.......................#############..........................#############...#
				#.......................................####################...#############...#
				#...#######...#######...................####################...#############...#
				#...#######...#######...................####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#...#######...#######...#############...####################...#############...#
				#..............................................................................#
				#..............................................................................#
				#..............................................................................#
				################################################################################
				""")
		self.assertEqual(dungeon.strata.tostring(lambda c: dungeon.TERRAIN[c.terrain].sprite), expected)
	def should_run_main_loop(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
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
			dungeon.main_loop(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			] + [ # MOVE MOVE DESCEND WALK_TO
			'redraw',
			'user_action',
			] * 4 + [ # walking...
			'redraw',
			'user_interrupted',
			] * 2 + ['redraw'] + [ # NONE AUTOEXPLORE
			'redraw',
			'user_action',
			] * 2 + [ # exploring...
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
	def should_suicide_out_of_main_loop(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		mock_ui = MockUI(user_actions=[
			(ui.Action.SUICIDE, None),
			], interrupts=[],
		)
		with mock_ui:
			dungeon.main_loop(mock_ui)
		self.assertFalse(dungeon.get_player().is_alive())
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'__exit__',
			])
	def should_get_visible_surroundings(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
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
	def should_move_player_character(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		dungeon.move(game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(9, 5))
		dungeon.move(game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(10, 5))
		dungeon.move(game.Direction.DOWN), 
		self.assertEqual(dungeon.get_player().pos, Point(10, 6))
		dungeon.move(game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		dungeon.move(game.Direction.UP_LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(8, 5))
		dungeon.move(game.Direction.DOWN_LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(7, 6))
		dungeon.move(game.Direction.DOWN_RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(8, 7))
		dungeon.move(game.Direction.UP_RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertEqual(dungeon.tostring(), textwrap.dedent(self._MockBuilder.MAP_DATA))
	def should_update_fov_after_movement(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
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
		dungeon.move(game.Direction.RIGHT) 
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
		dungeon.move(game.Direction.UP_RIGHT) 
		dungeon.move(game.Direction.UP) 
		dungeon.move(game.Direction.UP) 
		dungeon.move(game.Direction.UP) 
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
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))

		dungeon.move(game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
		dungeon.move(game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(0, 0))
	def should_not_move_player_into_a_wall(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				#####
				#.@.#
				#..>#
				#####
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.move(game.Direction.UP), 
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		dungeon.move(game.Direction.LEFT), 
		self.assertEqual(dungeon.get_player().pos, Point(1, 1))
	def should_move_player_through_a_wall_in_noclip_mode(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#.@#.#
				#...>#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.god.noclip = True
		dungeon.move(game.Direction.RIGHT), 
		self.assertEqual(dungeon.get_player().pos, Point(3, 1))
		dungeon.move(game.Direction.RIGHT), 
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
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(1, 1))

		self.assertFalse(dungeon.move(game.Direction.RIGHT))
		self.assertTrue(dungeon.move(game.Direction.DOWN))
		self.assertFalse(dungeon.move(game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move(game.Direction.DOWN))
		self.assertTrue(dungeon.move(game.Direction.RIGHT))
		self.assertFalse(dungeon.move(game.Direction.UP_RIGHT))
		self.assertFalse(dungeon.move(game.Direction.UP_LEFT))
		self.assertTrue(dungeon.move(game.Direction.RIGHT))
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
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockBuilder])
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
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockBuilder])
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
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(1, 1))

		self.assertTrue(dungeon.move(game.Direction.RIGHT))
		self.assertFalse(dungeon.move(game.Direction.DOWN_RIGHT))
		self.assertTrue(dungeon.move(game.Direction.DOWN))
		self.assertTrue(dungeon.move(game.Direction.RIGHT))
		self.assertTrue(dungeon.move(game.Direction.RIGHT))
		self.assertFalse(dungeon.move(game.Direction.UP_RIGHT))
		self.assertTrue(dungeon.move(game.Direction.RIGHT))
		self.assertTrue(dungeon.move(game.Direction.UP))
		self.assertEqual(dungeon.get_player().pos, Point(5, 1))
		self.assertFalse(dungeon.move(game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move(game.Direction.DOWN))
		self.assertTrue(dungeon.move(game.Direction.LEFT))
		self.assertTrue(dungeon.move(game.Direction.LEFT))
		self.assertFalse(dungeon.move(game.Direction.DOWN_LEFT))
		self.assertTrue(dungeon.move(game.Direction.LEFT))
		self.assertTrue(dungeon.move(game.Direction.DOWN))
		self.assertEqual(dungeon.get_player().pos, Point(2, 3))
	def should_reduce_visibility_at_dark_tiles(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				+--+ #
				|@.| #
				|..^##
				|.>|  
				+--+  
				"""
		dungeon = MockDarkRogueDungeon(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				+--+  
				|@.|  
				|..^  
				|.>|  
				+--+  
				"""))
		dungeon.move(game.Direction.RIGHT)
		dungeon.move(game.Direction.DOWN)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				+--+  
				|..|  
				|.@^  
				|.>|  
				+--+  
				"""))
		dungeon.move(game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				+--   
				|..|  
				|..@# 
				|.>|  
				+--   
				"""))
		dungeon.move(game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_     
				_  | #
				_  ^@#
				_ >|  
				_     
				""").replace('_', ' '))
		dungeon.move(game.Direction.RIGHT)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_     
				_    #
				_   #@
				_ >   
				_     
				""").replace('_', ' '))
		dungeon.move(game.Direction.UP)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_    #
				_    @
				_   ##
				_ >   
				_     
				""").replace('_', ' '))
		dungeon.move(game.Direction.UP)
		self.assertEqual(dungeon.tostring(with_fov=True), textwrap.dedent("""\
				_    @
				_    #
				_     
				_ >   
				_     
				""").replace('_', ' '))
	def should_descend_to_new_map(self):
		class _MockBuilder(builders.CustomMap):
			MAP_DATA = """\
				######
				#.@>.#
				#....#
				######
				"""
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.descend()
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		dungeon.move(game.Direction.RIGHT), 
		dungeon.descend()
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))
		self.assertEqual(dungeon.tostring(), textwrap.dedent(_MockBuilder.MAP_DATA))
	def should_directly_jump_to_new_position(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
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
	def should_auto_walk_to_position(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertFalse(dungeon.perform_automovement())
		dungeon.walk_to(Point(11, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Notices stairs and stops.
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
		dungeon = MockGame(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(2, 1))

		dungeon.walk_to(Point(4, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertEqual(dungeon.get_player().pos, Point(3, 2))
	def should_autoexplore(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))

		self.assertFalse(dungeon.perform_automovement())
		self.assertTrue(dungeon.start_autoexploring())
		for _ in range(12):
			self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Notices stairs and stops.
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

class TestSerialization(unittest.TestCase):
	class _MockMap(builders.CustomMap):
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
	@mock.patch('os.stat')
	@mock.patch('os.path.exists', side_effect=[False, True])
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_get_last_save_time(self, mock_filename, os_path_exists, os_stat):
		os_stat.return_value.st_mtime = 123
		self.assertEqual(game.Savefile.last_save_time(), 0)
		self.assertEqual(game.Savefile.last_save_time(), 123)
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_load_game_from_non_existent_file(self, mock_filename, os_path_exists):
		savefile = game.Savefile()
		self.assertEqual(savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		result = savefile.load()
		self.assertEqual(result, None)
	@mock.patch('clckwrkbdgr.rogue.game.load_game')
	@mock.patch('os.path.exists', side_effect=[True])
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_load_game_from_file_if_exists(self, mock_filename, os_path_exists, load_game):
		self.assertEqual(game.Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		load_game.side_effect = lambda _game_object, version, data: setattr(_game_object, '_data', list(data))
		stream = mock.mock_open(read_data='{0}\x00123\x00game data'.format(game.Version.CURRENT))
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = game.Savefile()
			game_object = savefile.load()
			self.assertEqual(game_object.rng.seed, 123)
			self.assertEqual(game_object._data, ["game data"])

			load_game.assert_called_once_with(game_object, game.Version.CURRENT, mock.ANY)
			stream.assert_called_once_with(game.Savefile.FILENAME, 'r')
			handle = stream()
			handle.read.assert_called_once()
	@mock.patch('clckwrkbdgr.rogue.game.save_game')
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_save_game_to_file(self, mock_filename, save_game):
		self.assertEqual(game.Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		save_game.side_effect = lambda game_object: (_ for _ in [game_object._data])
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = game.Savefile()
			game_object = game.Game(dummy=True)
			game_object._data = "game data"
			game_object.rng = RNG(123)
			savefile.save(game_object)

			stream.assert_called_once_with(game.Savefile.FILENAME, 'w')
			handle = stream()
			handle.write.assert_has_calls([
				mock.call('{0}\x00'.format(game.Version.CURRENT)),
				mock.call('123\x00'),
				mock.call('game data'),
				])
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[True])
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_unlink_save_file_if_exists(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(game.Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		savefile = game.Savefile()
		savefile.unlink()
		os_unlink.assert_called_once_with(game.Savefile.FILENAME)
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_unlink_save_file_if_does_not_exist(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(game.Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		savefile = game.Savefile()
		savefile.unlink()
		os_unlink.assert_not_called()

	def should_deserialize_game_before_terrain_types(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockMap])
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
		dump = list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		game.load_game(restored_dungeon, game.Version.TERRAIN_TYPES, iter(dump))
		self.assertEqual(dungeon.get_player().pos, restored_dungeon.get_player().pos)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).sprite, restored_dungeon.terrain_at(pos.x, pos.y).sprite, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).passable, restored_dungeon.terrain_at(pos.x, pos.y).passable, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).remembered, restored_dungeon.terrain_at(pos.x, pos.y).remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_monsters(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockMap])
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
		dump = list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		game.load_game(restored_dungeon, game.Version.MONSTERS, iter(dump))
		self.assertEqual(dungeon.get_player().pos, restored_dungeon.get_player().pos)
		self.assertEqual(restored_dungeon.get_player().hp, 10)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).sprite, restored_dungeon.terrain_at(pos.x, pos.y).sprite, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).passable, restored_dungeon.terrain_at(pos.x, pos.y).passable, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).remembered, restored_dungeon.terrain_at(pos.x, pos.y).remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_deserialize_game_before_behavior(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockMap])
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
			1, 'player', 9, 6, 10, 
			]
		dump = list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		game.load_game(restored_dungeon, game.Version.MONSTER_BEHAVIOR, iter(dump))
		self.assertEqual(dungeon.get_player().pos, restored_dungeon.get_player().pos)
		self.assertEqual(restored_dungeon.get_player().hp, 10)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).sprite, restored_dungeon.terrain_at(pos.x, pos.y).sprite, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).passable, restored_dungeon.terrain_at(pos.x, pos.y).passable, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).remembered, restored_dungeon.terrain_at(pos.x, pos.y).remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
	def should_serialize_and_deserialize_game(self):
		dungeon = MockGame(rng_seed=0, builders=[self._MockMap])
		dump = list(game.save_game(dungeon))
		self.assertEqual(dump, [
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
			1, 'player', 0, 9, 6, 10, 
			])
		dump = list(map(str, dump))
		restored_dungeon = MockGame(dummy=True)
		self.assertEqual(game.Version.CURRENT, 5)
		game.load_game(restored_dungeon, game.Version.CURRENT, iter(dump))
		self.assertEqual(dungeon.monsters, restored_dungeon.monsters)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).sprite, restored_dungeon.terrain_at(pos.x, pos.y).sprite, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).passable, restored_dungeon.terrain_at(pos.x, pos.y).passable, str(pos))
			self.assertEqual(dungeon.terrain_at(pos.x, pos.y).remembered, restored_dungeon.terrain_at(pos.x, pos.y).remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)

class TestMain(unittest.TestCase):
	@mock.patch('clckwrkbdgr.rogue.game.Savefile')
	@mock.patch('clckwrkbdgr.rogue.ui.auto_ui')
	@mock.patch('clckwrkbdgr.rogue.game.Game')
	def should_run_new_game(self, mock_game, mock_ui, mock_savefile):
		mock_savefile.return_value.load.return_value = None
		game.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.update_vision.assert_not_called()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
		mock_savefile.return_value.save.assert_called_once_with(mock_game.return_value)
	@mock.patch('clckwrkbdgr.rogue.game.Savefile')
	@mock.patch('clckwrkbdgr.rogue.ui.auto_ui')
	@mock.patch('clckwrkbdgr.rogue.game.Game')
	def should_load_game(self, mock_game, mock_ui, mock_savefile):
		mock_savefile.return_value.load.return_value = mock_game.return_value
		game.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.update_vision.assert_called_once_with()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
		mock_savefile.return_value.save.assert_called_once_with(mock_game.return_value)
	@mock.patch('clckwrkbdgr.rogue.game.Savefile')
	@mock.patch('clckwrkbdgr.rogue.ui.auto_ui')
	@mock.patch('clckwrkbdgr.rogue.game.Game')
	def should_abandon_game(self, mock_game, mock_ui, mock_savefile):
		mock_savefile.return_value.load.return_value = mock_game.return_value
		mock_game.return_value.get_player.return_value.is_alive.return_value = False
		game.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.update_vision.assert_called_once_with()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
		mock_savefile.return_value.save.assert_not_called()
		mock_savefile.return_value.unlink.assert_called_once_with()
