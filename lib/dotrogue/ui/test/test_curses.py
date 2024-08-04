import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from .. import curses, _base
from ...pcg import builders
from ... import game
from ...math import Point

class MockGame(game.Game):
	TERRAIN = {
		None : game.Terrain(' ', False),
		'#' : game.Terrain("#", False, remembered='#'),
		'.' : game.Terrain(".", True),
		'~' : game.Terrain(".", True, allow_diagonal=False),
		}

class MockCurses:
	class SubCall:
		def __init__(self, name, parent):
			self.name = name
			self.parent = parent
		def __call__(self, *args, **kwargs):
			self.parent.calls.append((self.name,) + args + ((kwargs,) if kwargs else tuple()))
	def __init__(self, chars=None):
		self.calls = []
		self.chars = [(ord(c) if isinstance(c, str) else c) for c in (chars or [])]
	def getch(self):
		return self.chars.pop(0)
	def __getattr__(self, name):
		return self.SubCall(name, self)

class TestCurses(unittest.TestCase):
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
	DISPLAYED_LAYOUT = [
			'    #####        #  ',
			'     ....   #  ...  ',
			'      ...  .# ..... ',
			'     ##..##.#...... ',
			'     #............. ',
			'#.M..#............. ',
			'#........@.........#',
			'#.................. ',
			'#.................. ',
			' #################  ',
			]
	DISPLAYED_LAYOUT_FULL = [
			'####################',
			'#........#>##......#',
			'#........#..#......#',
			'#....##..##.#......#',
			'#....#.............#',
			'#.M..#.............#',
			'#........@.........#',
			'#..................#',
			'#..................#',
			'####################',
			]

	def should_draw_game(self):
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.calls, [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 24, 0, '                                                                                '),
			('refresh',),
			])
	def should_show_state_markers(self):
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		dungeon.movement_queue = ['mock']

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.calls, [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 24, 0, '[auto]                                                                          '),
			('refresh',),
			])

		ui.window = MockCurses()
		dungeon.movement_queue = []
		dungeon.god.vision = True
		dungeon.god.noclip = True

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.calls, [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 24, 0, '[vis] [clip]                                                                    '),
			('refresh',),
			])
	@mock.patch('curses.curs_set')
	def should_display_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('x')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		curs_set.assert_has_calls([
			mock.call(1),
			])

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.calls, [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 24, 0, '                                                                                '),
			('move', 7, 9),
			('refresh',),
			])
	def should_check_for_user_interrupt(self):
		ui = curses.Curses()
		ui.window = MockCurses([-1, -1, ' '])
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])

		self.assertFalse(ui.user_interrupted())
		self.assertFalse(ui.user_interrupted())
		self.assertTrue(ui.user_interrupted())
	def should_exit(self):
		ui = curses.Curses()
		ui.window = MockCurses('q')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.EXIT, None))
	@mock.patch('curses.curs_set')
	def should_enable_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('x')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, dungeon.get_player().pos)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	@mock.patch('curses.curs_set')
	def should_cancel_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('x')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		ui.aim = dungeon.get_player().pos
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertIsNone(ui.aim)
		curs_set.assert_has_calls([
			mock.call(0),
			])
	@mock.patch('curses.curs_set')
	def should_select_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('.x.')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.WALK_TO, Point(9, 6)))
		self.assertIsNone(ui.aim)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	def should_autoexplore(self):
		ui = curses.Curses()
		ui.window = MockCurses('o')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.AUTOEXPLORE, None))
	def should_toggle_god_settings(self):
		ui = curses.Curses()
		ui.window = MockCurses('~Q~v~c')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.GOD_TOGGLE_VISION, None))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.GOD_TOGGLE_NOCLIP, None))
	def should_suicide(self):
		ui = curses.Curses()
		ui.window = MockCurses('Q')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.SUICIDE, None))
	def should_descend(self):
		ui = curses.Curses()
		ui.window = MockCurses('>')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.DESCEND, None))
	def should_move_character(self):
		ui = curses.Curses()
		ui.window = MockCurses('hjklyubn')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.LEFT))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.DOWN))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.UP))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.RIGHT))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.UP_LEFT))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.UP_RIGHT))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.DOWN_LEFT))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.DOWN_RIGHT))
	@mock.patch('curses.curs_set')
	def should_move_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('xhjklyubn')
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder])
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(9, 6))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(8, 6))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(8, 7))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(8, 6))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(9, 6))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(8, 5))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(9, 4))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(8, 5))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, Point(9, 6))
