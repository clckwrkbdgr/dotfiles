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
	def _build(self):
		self._map_data = self._map_data.splitlines()
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

class TestDungeon(unittest.TestCase):
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
		builder.add_cell_type('#', MockCell, "#", False, remembered='+')
		builder.add_cell_type('$', MockCell, "$", False, remembered='+', visited=True)
		builder.add_cell_type('.', MockCell, ".", True)
		builder.add_cell_type('!', MockCell, ".", True, visited=True)
		builder.add_cell_type('@', MockCell, ".", True, visited=True)
		builder.build()

		path = game.autoexplore(builder.start_pos, builder.strata)
		self.assertEqual(path, [
			Point(x=9, y=6), Point(x=8, y=5), Point(x=7, y=4),
			])

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
		load_game.side_effect = lambda version, data: (version, list(data))
		stream = mock.mock_open(read_data='{0}\x00123\x00game data'.format(game.Version.CURRENT))
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = game.Savefile()
			rng, game_object = savefile.load()
			self.assertEqual(rng.seed, 123)
			self.assertEqual(game_object, (game.Version.CURRENT, ["game data"]))

			stream.assert_called_once_with(game.Savefile.FILENAME, 'r')
			handle = stream()
			handle.read.assert_called_once()
	@mock.patch('clckwrkbdgr.rogue.game.save_game')
	@mock.patch('clckwrkbdgr.rogue.game.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_save_game_to_file(self, mock_filename, save_game):
		self.assertEqual(game.Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		save_game.side_effect = lambda game_object: (_ for _ in [str(game_object)])
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = game.Savefile()
			game_object = "game data"
			rng = RNG(123)
			savefile.save(rng, game_object)

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
	def should_serialize_and_deserialize_game(self):
		rng = RNG(0)
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
		builder.add_cell_type('#', MockCell, "#", False, remembered='+')
		builder.add_cell_type('$', MockCell, "$", False, remembered='+', visited=True)
		builder.add_cell_type('.', MockCell, ".", True)
		builder.add_cell_type('!', MockCell, ".", True, visited=True)
		builder.add_cell_type('@', MockCell, ".", True, visited=True)
		builder.add_cell_type('>', MockCell, ".", True)
		builder.build()

		dungeon = game.Game(builder.start_pos, builder.exit_pos, builder.strata)
		dump = list(game.save_game(dungeon))
		self.assertEqual(dump, [
			9, 6, 10, 1, 0, 20, 10,
			'#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0,
			'#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0,
			'#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '#', 0, '+', 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0,
			'.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 1, '$', 0, '+', 1, '$', 0, '+', 1,
			'.', 1, None, 1, '$', 0, '+', 1, '.', 1, None, 1, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'#', 0, '+', 0, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1,
			'.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0,
			'#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '$', 0, '+', 1,
			'.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1,
			'.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0,
			'+', 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1,
			'.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1,
			'.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 0, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1,
			'.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 1, '.', 1, None, 0, '.', 1, None, 0,
			'.', 1, None, 0, '.', 1, None, 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0,
			'+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0,
			'#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0, '#', 0, '+', 0,
			])
		dump = list(map(str, dump))
		restored_dungeon = game.load_game(game.Version.CURRENT, iter(dump))
		self.assertEqual(dungeon.player, restored_dungeon.player)
		self.assertEqual(dungeon.exit_pos, restored_dungeon.exit_pos)
		for pos in dungeon.strata.size:
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).sprite, restored_dungeon.strata.cell(pos.x, pos.y).sprite, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).passable, restored_dungeon.strata.cell(pos.x, pos.y).passable, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).remembered, restored_dungeon.strata.cell(pos.x, pos.y).remembered, str(pos))
			self.assertEqual(dungeon.strata.cell(pos.x, pos.y).visited, restored_dungeon.strata.cell(pos.x, pos.y).visited, str(pos))
		self.assertEqual(dungeon.remembered_exit, restored_dungeon.remembered_exit)
