import contextlib
from clckwrkbdgr import unittest
from clckwrkbdgr.math import Point, Size, Rect, Matrix
from ..game import Game
from ..dungeon import Dungeon
from ..builders import EndlessFloor, EndlessWall

class MockUI:
	def __init__(self, scheduled_controls):
		self.controls = scheduled_controls
		self.tiles = Matrix((25, 25), ' ')
		self.lines = {}
	def print_char(self, x, y, tile, color):
		self.tiles.set_cell((x, y), tile)
	def print_line(self, index, _col, line):
		self.lines[index] = line
	@contextlib.contextmanager
	def redraw(self, clean=None):
		yield self
	def get_control(self, _keymapping, nodelay=False, bind_self=None, callback_args=None):
		return self.controls.pop(0)

class MockExplorer:
	def __init__(self, controls):
		self.controls = controls
	def next(self):
		return self.controls.pop(0)

class MockBuilder:
	def __init__(self, rogue_pos=None, walls=None):
		self.rogue_pos = rogue_pos or (0, 0)
		self.walls = walls or []
	def build_block(self, block):
		block.clear(EndlessFloor())
		if not self.walls:
			return
		walls = self.walls.pop(0)
		for wall in walls:
			block.set_cell(wall, EndlessWall())
	def place_rogue(self, terrain):
		return self.rogue_pos

class TestGame(unittest.TestCase):
	def _create_dungeon(self):
		dungeon = Dungeon(builder=MockBuilder(walls=[[]]*4+[[(2, 3)]]))
		dungeon.generate()
		return dungeon
	def _extract_matrix(self, m, source):
		result = Matrix(source.size, ' ')
		for x in range(source.left, source.right+1):
			for y in range(source.top, source.bottom+1):
				result.set_cell(Point(x, y) - source.topleft,
						  m.cell((x, y)),
						  )
		return result

	def _compare_matrices(self, a, b, msg=None): # pragma: no cover -- TODO move to definition of Matrix.
		if a == b:
			return
		import difflib
		msg = "{0} != {1}: {2}\n".format(repr(a), repr(b), msg or '')
		msg += ''.join(difflib.unified_diff(
			a.tostring().splitlines(True),
			b.tostring().splitlines(True),
			"expected",
			"actual",
			))
		raise self.failureException(msg)
	def setUp(self):
		self.addTypeEqualityFunc(Matrix, self._compare_matrices)

	def should_start_game_and_exit(self):
		ui = MockUI(['quit'])
		dungeon = self._create_dungeon()
		game = Game(dungeon)
		game.run(game, ui)
	def should_draw_game_and_print_info(self):
		ui = MockUI(['quit'])
		dungeon = self._create_dungeon()
		game = Game(dungeon)
		game.run(game, ui)

		expected = Matrix((25, 25), '.')
		expected.set_cell((12, 12), '@')
		expected.set_cell((14, 15), '#')
		self.assertEqual(ui.tiles, expected)
		self.assertEqual(ui.lines, {
			0: 'Time: 0',
			1: 'X:0 Y:0  ',
			24: '                             ',
			})
	def should_control_dungeon_via_ui(self):
		ui = MockUI([Point(0, 1), Point(0, 1), Point(1, 1), Point(1, 0), 'quit'])
		dungeon = self._create_dungeon()
		game = Game(dungeon)
		game.run(game, ui)

		expected = Matrix((25, 25), '.')
		expected.set_cell((12, 12), '@')
		expected.set_cell((13, 12), '#')
		self.assertEqual(
				self._extract_matrix(ui.tiles, Rect((10, 10), (5, 5))),
				self._extract_matrix(expected, Rect((10, 10), (5, 5))),
				)
		self.assertEqual(ui.lines, {
			0: 'Time: 4',
			1: 'X:1 Y:3  ',
			24: '                             ',
			})
	def should_pass_on_unknown_control(self):
		ui = MockUI([None, 'unknown', 'quit'])
		dungeon = self._create_dungeon()
		game = Game(dungeon)
		game.run(game, ui)
	def should_control_dungeon_via_autoexplorer(self):
		autoexplorer_controls = [
			Point(0, 1), Point(0, 1), Point(1, 1), Point(1, 0),
			]
		ui = MockUI(['autoexplore'] + ['autoexplore'] * len(autoexplorer_controls) + ['ESC', 'quit'])
		dungeon = self._create_dungeon()
		game = Game(dungeon, autoexplorer=lambda _: MockExplorer(autoexplorer_controls))
		game.run(game, ui)

		expected = Matrix((25, 25), '.')
		expected.set_cell((12, 12), '@')
		expected.set_cell((13, 12), '#')
		self.assertEqual(
				self._extract_matrix(ui.tiles, Rect((10, 10), (5, 5))),
				self._extract_matrix(expected, Rect((10, 10), (5, 5))),
				)
		self.assertEqual(ui.lines, {
			0: 'Time: 4',
			1: 'X:1 Y:3  ',
			24: '                             ',
			})
