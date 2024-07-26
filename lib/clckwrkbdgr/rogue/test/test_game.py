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

class MockCell(game.Cell):
	def __init__(self, *args, **kwargs):
		visited = False
		if 'visited' in kwargs:
			visited = kwargs['visited']
			del kwargs['visited']
		super(MockCell, self).__init__(*args, **kwargs)
		self.visited = visited

class StrBuilder(builders.Builder):
	""" Set ._map_data to multiline string (one char for each cell).
	Register cell types according to those chars.
	Set char to '@' to indicate start pos.
	Set char to '>' to indicate exit pos.
	"""
	def __init__(self, rng, map_size):
		if hasattr(self, '_map_size'):
			map_size = self._map_size
		super(StrBuilder, self).__init__(rng, map_size)
	def _build(self):
		self._map_data = self._map_data.splitlines()

		self.add_cell_type(None, game.Cell, ' ', False)
		self.add_cell_type('#', MockCell, "#", False, remembered='#')
		self.add_cell_type('.', MockCell, ".", True)
		self.add_cell_type('@', MockCell, ".", True, visited=True)
		self.add_cell_type('>', MockCell, ".", True)

		for x in range(self.size.width):
			for y in range(self.size.height):
				self.strata.set_cell(x, y, self._map_data[y][x])
				if self._map_data[y][x] == '@':
					self.start_pos = Point(x, y)
				elif self._map_data[y][x] == '>':
					self.exit_pos = Point(x, y)

class MockBuilder(builders.Builder):
	def _build(self):
		for x in range(self.size.width):
			self.strata.set_cell(x, 0, 'wall')
			self.strata.set_cell(x, self.size.height - 1, 'wall')
		for y in range(self.size.height):
			self.strata.set_cell(0, y, 'wall')
			self.strata.set_cell(self.size.width - 1, y, 'wall')
		for x in range(1, self.size.width - 1):
			for y in range(1, self.size.height - 1):
				self.strata.set_cell(x, y, 'floor')
		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) == 'floor'
		obstacle_pos = pcg.pos(self.rng, self.size, floor_only)
		self.strata.set_cell(obstacle_pos.x, obstacle_pos.y, 'wall')

		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		self.exit_pos = pcg.pos(self.rng, self.size, floor_only)

		# Room.
		room_pos = pcg.pos(self.rng, Size(self.size.width - 6, self.size.height - 5), floor_only)
		room_width = self.rng.range(3, 5)
		room_height = self.rng.range(3, 4)
		for x in range(room_width):
			self.strata.set_cell(room_pos.x + x, room_pos.y + 0, 'wall_h')
			self.strata.set_cell(room_pos.x + x, room_pos.y + room_height - 1, 'wall_h')
		for y in range(room_height):
			self.strata.set_cell(room_pos.x + 0, room_pos.y + y, 'wall_v')
			self.strata.set_cell(room_pos.x + room_width - 1, room_pos.y + y, 'wall_v')
		for x in range(1, room_width - 1):
			for y in range(1, room_height - 1):
				self.strata.set_cell(room_pos.x + x, room_pos.y + y, 'water')
		self.strata.set_cell(room_pos.x, room_pos.y, 'corner')
		self.strata.set_cell(room_pos.x, room_pos.y + room_height - 1, 'corner')
		self.strata.set_cell(room_pos.x + room_width - 1, room_pos.y, 'corner')
		self.strata.set_cell(room_pos.x + room_width - 1, room_pos.y + room_height - 1, 'corner')
		door_pos = self.rng.range(1, 4)
		self.strata.set_cell(room_pos.x + door_pos, room_pos.y, 'door')

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
	def _str_dungeon(self, dungeon, with_fov=False):
		result = ""
		for y in range(dungeon.strata.size.height):
			for x in range(dungeon.strata.size.width):
				if dungeon.player.x == x and dungeon.player.y == y:
					result += "@"
				elif dungeon.exit_pos.x == x and dungeon.exit_pos.y == y:
					result += ">"
				else:
					if with_fov and not dungeon.field_of_view.is_visible(x, y):
						result += dungeon.strata.cell(x, y).remembered or ' '
					else:
						result += dungeon.strata.cell(x, y).sprite
			result += "\n"
		return result
	def should_create_new_dungeon(self):
		dungeon = game.Game(rng_seed=123)
		self.assertEqual(dungeon.player, Point(17, 21))
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
		self.assertEqual(dungeon.strata.tostring(lambda c: c.sprite), expected)
	def should_build_dungeon(self):
		rng = RNG(0)
		builder = game.build_dungeon(MockBuilder, rng, Size(20, 20))
		self.assertEqual(builder.start_pos, Point(9, 12))
		self.assertEqual(builder.exit_pos, Point(7, 16))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				####################
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#........+-++......#
				#........|~~|......#
				#.....#..+--+......#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				####################
				""")
		self.assertEqual(builder.strata.tostring(lambda c: c.sprite), expected)
	def should_run_main_loop(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
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
			], interrupts=[False] * 3 + [False] * 10 + [True] + [False] * 5,
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
			] * 3 + ['redraw'] + [ # NONE AUTOEXPLORE
			'redraw',
			'user_action',
			] * 2 + [ # exploring...
			'redraw',
			'user_interrupted',
			] * 11 + ['redraw', 'user_action'] + [ # AUTOEXPLORE
			'redraw',
			'user_interrupted',
			] * 5 + ['redraw'] + [ # GOD_TOGGLE_* EXIT
			'redraw',
			'user_action',
			] * 3 + [
			'__exit__',
			])
	def should_suicide_out_of_main_loop(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		mock_ui = MockUI(user_actions=[
			(ui.Action.SUICIDE, None),
			], interrupts=[],
		)
		with mock_ui:
			dungeon.main_loop(mock_ui)
		self.assertFalse(dungeon.alive)
		self.maxDiff = None
		self.assertEqual(mock_ui.events, [
			'__enter__',
			'redraw',
			'user_action',
			'__exit__',
			])
	def should_autoexplore_map(self):
		rng = RNG(0)
		builder = StrBuilder(rng, Size(20, 10))
		builder._map_data = textwrap.dedent("""\
				####################
				#........#.##......#
				#........#..#......#
				#....##.!$$!$!.....#
				#....#!!!!!!!!!....#
				#....$!!!!!!!!!....#
				#....!!!!@!!!!!....#
				#....!!!!!!!!!!....#
				#.....!!!!!!!!!....#
				####################
				""")
		builder.add_cell_type(None, game.Cell, ' ', False)
		builder.add_cell_type('#', MockCell, "#", False, remembered='#')
		builder.add_cell_type('$', MockCell, "$", False, remembered='#', visited=True)
		builder.add_cell_type('.', MockCell, ".", True)
		builder.add_cell_type('!', MockCell, ".", True, visited=True)
		builder.add_cell_type('@', MockCell, ".", True, visited=True)
		builder.build()

		path = game.autoexplore(builder.start_pos, builder.strata)
		self.assertEqual(path, [
			Point(x=9, y=6), Point(x=8, y=5), Point(x=7, y=4),
			])
	def should_get_visible_surroundings(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
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
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(9, 6))

		dungeon.move(game.Direction.UP), 
		self.assertEqual(dungeon.player, Point(9, 5))
		dungeon.move(game.Direction.RIGHT), 
		self.assertEqual(dungeon.player, Point(10, 5))
		dungeon.move(game.Direction.DOWN), 
		self.assertEqual(dungeon.player, Point(10, 6))
		dungeon.move(game.Direction.LEFT), 
		self.assertEqual(dungeon.player, Point(9, 6))

		dungeon.move(game.Direction.UP_LEFT), 
		self.assertEqual(dungeon.player, Point(8, 5))
		dungeon.move(game.Direction.DOWN_LEFT), 
		self.assertEqual(dungeon.player, Point(7, 6))
		dungeon.move(game.Direction.DOWN_RIGHT), 
		self.assertEqual(dungeon.player, Point(8, 7))
		dungeon.move(game.Direction.UP_RIGHT), 
		self.assertEqual(dungeon.player, Point(9, 6))

		self.assertEqual(self._str_dungeon(dungeon), _MockBuilder._map_data)
	def should_update_fov_after_movement(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(9, 6))

		self.assertFalse(dungeon.remembered_exit)
		self.assertEqual(self._str_dungeon(dungeon, with_fov=True), textwrap.dedent("""\
				####################
				#    ....#>##  ... #
				#     ...# .# .....#
				#    ##..##.#......#
				#    #.............#
				#....#.............#
				#........@.........#
				#..................#
				#..................#
				####################
				"""))
		dungeon.move(game.Direction.RIGHT) 
		self.assertFalse(dungeon.remembered_exit)
		self.assertEqual(self._str_dungeon(dungeon, with_fov=True), textwrap.dedent("""\
				####################
				#    ... #>## .....#
				#     ...# .#......#
				#    ##..##.#......#
				#    #.............#
				#    #.............#
				#.........@........#
				#..................#
				#..................#
				####################
				"""))
		dungeon.move(game.Direction.UP_RIGHT) 
		dungeon.move(game.Direction.UP) 
		dungeon.move(game.Direction.UP) 
		dungeon.move(game.Direction.UP) 
		self.assertTrue(dungeon.remembered_exit)
		self.assertEqual(self._str_dungeon(dungeon, with_fov=True), textwrap.dedent("""\
				####################
				#        #>##      #
				#        #.@#      #
				#    ##  ##.#      #
				#    #    ...      #
				#    #    ...      #
				#        .....     #
				#        .....     #
				#       .......    #
				####################
				"""))
	def should_not_move_player_into_the_void(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
				@...#
				....#
				...>#
				#####
				""")
			_map_size = Size(5, 4)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(0, 0))

		dungeon.move(game.Direction.UP), 
		self.assertEqual(dungeon.player, Point(0, 0))
		dungeon.move(game.Direction.LEFT), 
		self.assertEqual(dungeon.player, Point(0, 0))
	def should_not_move_player_into_a_wall(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
				#####
				#.@.#
				#..>#
				#####
				""")
			_map_size = Size(5, 4)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(2, 1))

		dungeon.move(game.Direction.UP), 
		self.assertEqual(dungeon.player, Point(2, 1))
		dungeon.move(game.Direction.LEFT), 
		self.assertEqual(dungeon.player, Point(1, 1))
	def should_move_player_through_a_wall_in_noclip_mode(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
				######
				#.@#.#
				#...>#
				######
				""")
			_map_size = Size(6, 4)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(2, 1))

		dungeon.god.noclip = True
		dungeon.move(game.Direction.RIGHT), 
		self.assertEqual(dungeon.player, Point(3, 1))
		dungeon.move(game.Direction.RIGHT), 
		self.assertEqual(dungeon.player, Point(4, 1))
	def should_descend_to_new_map(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
				######
				#.@>.#
				#....#
				######
				""")
			_map_size = Size(6, 4)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(2, 1))

		dungeon.descend()
		self.assertEqual(dungeon.player, Point(2, 1))
		dungeon.move(game.Direction.RIGHT), 
		dungeon.descend()
		self.assertEqual(dungeon.player, Point(2, 1))
		self.assertEqual(self._str_dungeon(dungeon), _MockBuilder._map_data)
	def should_directly_jump_to_new_position(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(9, 6))

		dungeon.jump_to(Point(11, 2))
		self.assertEqual(self._str_dungeon(dungeon, with_fov=True), textwrap.dedent("""\
				####################
				#        #>##      #
				#        #.@#      #
				#    ##  ##.#      #
				#    #    ...      #
				#    #    ...      #
				#        .....     #
				#        .....     #
				#       .......    #
				####################
				"""))
	def should_auto_walk_to_position(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(9, 6))

		self.assertFalse(dungeon.perform_automovement())
		dungeon.walk_to(Point(11, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Notices stairs and stops.
		self.assertFalse(dungeon.perform_automovement())

		dungeon.walk_to(Point(11, 2))
		self.assertTrue(dungeon.perform_automovement())
		self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # You have reached your destination.

		self.assertEqual(self._str_dungeon(dungeon, with_fov=True), textwrap.dedent("""\
				####################
				#        #>##      #
				#        #.@#      #
				#    ##  ##.#      #
				#    #    ...      #
				#    #    ...      #
				#        .....     #
				#        .....     #
				#       .......    #
				####################
				"""))
	def should_autoexplore(self):
		class _MockBuilder(StrBuilder):
			_map_data = textwrap.dedent("""\
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
				""")
			_map_size = Size(20, 10)
		dungeon = game.Game(rng_seed=0, builders=[_MockBuilder])
		self.assertEqual(dungeon.player, Point(9, 6))

		self.assertFalse(dungeon.perform_automovement())
		self.assertTrue(dungeon.start_autoexploring())
		for _ in range(15):
			self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Notices stairs and stops.
		self.assertFalse(dungeon.perform_automovement())

		self.assertTrue(dungeon.start_autoexploring())
		for _ in range(7):
			self.assertTrue(dungeon.perform_automovement())
		with self.assertRaises(dungeon.AutoMovementStopped):
			dungeon.perform_automovement() # Explored everything.

		self.assertFalse(dungeon.start_autoexploring()) # And Jesus wept.

		self.assertEqual(self._str_dungeon(dungeon, with_fov=True), textwrap.dedent("""\
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
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_load_game_from_non_existent_file(self, mock_filename, os_path_exists):
		savefile = game.Savefile()
		self.assertEqual(savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		result = savefile.load()
		self.assertEqual(result, (None, None))
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
	def _build_str_dungeon(self, _builder, rng, _size):
		builder = StrBuilder(rng, Size(20, 10))
		builder._map_data = textwrap.dedent("""\
				####################
				#........#>##......#
				#........#..#......#
				#....##.!$$!$!.....#
				#....#!!!!!!!!!....#
				#....$!!!!!!!!!....#
				#....!!!!@!!!!!....#
				#....!!!!!!!!!!....#
				#.....!!!!!!!!!....#
				####################
				""")
		builder.add_cell_type(None, game.Cell, ' ', False)
		builder.add_cell_type('#', MockCell, "#", False, remembered='#')
		builder.add_cell_type('$', MockCell, "$", False, remembered='#', visited=True)
		builder.add_cell_type('.', MockCell, ".", True)
		builder.add_cell_type('!', MockCell, ".", True, visited=True)
		builder.add_cell_type('@', MockCell, ".", True, visited=True)
		builder.add_cell_type('>', MockCell, ".", True)
		builder.build()
		return builder
	@mock.patch('clckwrkbdgr.rogue.game.build_dungeon')
	def should_serialize_and_deserialize_game(self, mock_build_dungeon):
		mock_build_dungeon.side_effect = self._build_str_dungeon
		dungeon = game.Game(rng_seed=0)
		dump = list(game.save_game(dungeon))
		self.assertEqual(dump, [
			9, 6, 10, 1, 0, 20, 10,
			'#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',0, '#',0,'#',1, '#',0,'#',0, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0, '.',1,None,0, '#',0,'#',0, '#',0,'#',1, '.',1,None,0, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,0, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0, '.',1,None,0, '.',1,None,1, '#',0,'#',1, '.',1,None,0, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '#',0,'#',1, '#',0,'#',1, '.',1,None,1, '.',1,None,1, '$',0,'#',1, '$',0,'#',1, '.',1,None,1, '$',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '.',1,None,0, '#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '$',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',1,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '.',1,None,1, '#',0,'#',0,
			'#',0,'#',0, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',1, '#',0,'#',0, '#',0,'#',0,
			])
		dump = list(map(str, dump))
		restored_dungeon = game.Game(dummy=True)
		game.load_game(restored_dungeon, game.Version.CURRENT, iter(dump))
		self.assertEqual(dungeon.player, restored_dungeon.player)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).sprite, restored_dungeon.strata.cell(pos.x, pos.y).sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).passable, restored_dungeon.strata.cell(pos.x, pos.y).passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).remembered, restored_dungeon.strata.cell(pos.x, pos.y).remembered, str(pos))
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
		mock_game.return_value.alive = False
		game.run()
		mock_savefile.assert_called_once_with()
		mock_savefile.return_value.load.assert_called_once_with()
		mock_game.return_value.update_vision.assert_called_once_with()
		mock_game.return_value.main_loop.assert_called_once_with(mock_ui.return_value.return_value.__enter__.return_value)
		mock_savefile.return_value.save.assert_not_called()
		mock_savefile.return_value.unlink.assert_called_once_with()
