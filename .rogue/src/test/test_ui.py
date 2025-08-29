import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from .. import ui
from ..ui import MainGame
from clckwrkbdgr.math import Point, Direction, Rect
from clckwrkbdgr import utils
from ..test import mock_dungeon
from ..test.mock_dungeon import MockGame
from clckwrkbdgr.tui import Key, ModeLoop, Curses
from ..engine.events import Event

class MockCurses:
	class SubCall:
		def __init__(self, name, parent):
			self.name = name
			self.parent = parent
		def __call__(self, *args, **kwargs):
			if self.name == 'addstr' and len(args) == 4 and args[3] == 0:
				args = args[:-1]
			self.parent.calls.append((self.name,) + args + ((kwargs,) if kwargs else tuple()))
	def __init__(self, chars=None):
		self.calls = []
		self.chars = [(ord(c) if isinstance(c, str) else c) for c in (chars or [])]
	def get_calls(self):
		result = self.calls
		self.calls = []
		return result
	def getch(self):
		return self.chars.pop(0)
	def __getattr__(self, name):
		return self.SubCall(name, self)

class TestCurses(unittest.TestCase):
	DISPLAYED_LAYOUT = [
			'    #####        #  ',
			'     ....   #  ...  ',
			'      ...  .# ..... ',
			'     ##..##.#M..... ',
			'     #............. ',
			'#....#............. ',
			'#........@.........#',
			'#.................. ',
			'#.................. ',
			' #################  ',
			]
	NEXT_DUNGEON = [
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
	DISPLAYED_LAYOUT_DEAD = [
			'    #####        #  ',
			'     ....   #  ...  ',
			'      ...  .# ..... ',
			'     ##..##.#M..... ',
			'     #............. ',
			'#....#............. ',
			'#..................#',
			'#.................. ',
			'#.................. ',
			' #################  ',
			]
	DISPLAYED_LAYOUT_EXIT = [
			'  #########      ###',
			'          >##    ..#',
			'          ..#  ....#',
			'     ##..##.#M.....#',
			'     #.....@.......#',
			'#    #.............#',
			'#  ................#',
			'# .................#',
			'# .................#',
			' ###################',
			]
	DISPLAYED_LAYOUT_REMEMBERED_EXIT = [
			'  #########      ###',
			'  ...     >##      #',
			'    ...    .#    ..#',
			'     ##..##.#M.....#',
			'     #....@........#',
			'#    #.............#',
			'#  ................#',
			'#..................#',
			'#..................#',
			' ###################',
			]
	DISPLAYED_LAYOUT_FIGHT = [
			'    #####   ########',
			'            #......#',
			'            #......#',
			'     ##..##.#M.....#',
			'     #.......@.....#',
			'#    #.............#',
			'#   ...............#',
			'#   ...............#',
			'#   ...............#',
			' ###################',
			]
	DISPLAYED_LAYOUT_FIGHT_THIEF = [
			'    #####   ########',
			'            #......#',
			'            #......#',
			'     ##..##.#T.....#',
			'     #.......@.....#',
			'#    #.............#',
			'#   ...............#',
			'#   ...............#',
			'#   ...............#',
			' ###################',
			]
	DISPLAYED_LAYOUT_KILLED_MONSTER = [
			'    #####   ########',
			'            #......#',
			'            #......#',
			'     ##..##.#......#',
			'     #.......@.....#',
			'#    #.............#',
			'#   ...............#',
			'#   ...............#',
			'#   ...............#',
			' ###################',
			]
	DISPLAYED_LAYOUT_FULL = [
			'####################',
			'#........#>##......#',
			'#........#..#......#',
			'#....##..##.#M.....#',
			'#....#.............#',
			'#....#.............#',
			'#........@.........#',
			'#..................#',
			'#..................#',
			'####################',
			]

	def _init(self, dungeon, key_sequence=None):
		main_mode = MainGame(dungeon)
		ui = Curses()
		loop = ModeLoop(ui)
		loop.modes.append(main_mode)
		ui.window = MockCurses(key_sequence)
		return ui, loop
	def _addstr_map(self, matrix):
		return [
			('addstr', y, x, matrix[y-1][x]) for y in range(1, 11) for x in range(20)
			if matrix[y-1][x] != ' '
			]

	def should_draw_game(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_show_state_markers(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)
		dungeon.automovement = True

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '[auto]'),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		dungeon.automovement = None
		dungeon.god.vision = True
		dungeon.god.noclip = True

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_FULL) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '[vis]'),
			('addstr', 24, 39, '[clip]'),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_display_discover_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, '.')

		dungeon.automove()
		# Monster is already spotted from the beginning,
		# now move into cave opening to detect exit.
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP_RIGHT)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP_RIGHT)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP_RIGHT)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_EXIT) + [
			('addstr', 0, 0, 'monster! monsters! stairs!                                                      '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
		
		list(dungeon.process_events(raw=True))
		self.assertTrue(loop.action())
		loop.redraw()
		self.maxDiff = None

		DISPLAYED_LAYOUT_EXIT = [
				'  #########      ###',
				'          >##    ..#',
				'          ..#  ....#',
				'     ##..##.#......#',
				'     #.....@M......#',
				'#    #.............#',
				'#  ................#',
				'# .................#',
				'# .................#',
				' ###################',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT_EXIT) + [
			('addstr', 0, 0, 'monster...                                                                      '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_display_remembered_exit(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, '.')

		dungeon.automove()
		# Monster is already spotted from the beginning,
		# now move into cave opening to detect exit.
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP_RIGHT)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP_RIGHT)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP_RIGHT)
		# Now move back and try to remember exit.
		dungeon.move_actor(dungeon.scene.get_player(), Direction.LEFT)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_REMEMBERED_EXIT) + [
			('addstr', 0, 0, 'monster! monsters! stairs!                                                      '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_display_attack_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)
		list(dungeon.process_events(raw=True))

		dungeon.jump_to(dungeon.scene.get_player(), Point(13, 4))
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_FIGHT) + [
			('addstr', 0, 0, 'player x> monster. monster-1hp.                                                 '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		# Finish him.
		list(dungeon.process_events(raw=True))
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_KILLED_MONSTER) + [
			('addstr', 0, 0, 'player x> monster. monster-1hp. player x> monster. monster-1hp. monster dies.   '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_display_movement_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)
		list(dungeon.process_events(raw=True))
		dungeon.god.vision = True

		dungeon.move_actor(dungeon.scene.get_player(), Direction.RIGHT)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.RIGHT)
		dungeon.move_actor(dungeon.scene.get_player(), Direction.RIGHT)

		dungeon.move_actor(dungeon.scene.monsters[-1], Direction.LEFT)

		loop.redraw()
		self.maxDiff = None
		DISPLAYED_LAYOUT_FULL = [
				'####################',
				'#........#>##......#',
				'#........#..#......#',
				'#....##..##.#M.....#',
				'#....#.............#',
				'#....#.............#',
				'#...........@......#',
				'#..................#',
				'#..................#',
				'####################',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT_FULL) + [
			('addstr', 0, 0, 'stairs! monster bumps.                                                          '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '[vis]'),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_wait_user_reaction_after_player_is_dead(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, ' ')
		list(dungeon.process_events(raw=True))

		dungeon.affect_health(dungeon.scene.get_player(), -dungeon.scene.get_player().hp)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_DEAD) + [
			('addstr', 0, 0, 'player-10hp. player dies.                                                       '),
			('addstr', 24, 0, '[DEAD] Press Any Key...'),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	@mock.patch('curses.curs_set')
	def should_display_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'x')

		list(dungeon.process_events(raw=True))
		self.assertTrue(loop.action())
		loop.redraw()
		curs_set.assert_has_calls([
			mock.call(1),
			])

		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('move', 7, 9),
			('refresh',),
			])
	def should_check_for_user_interrupt(self):
		dungeon = mock_dungeon.build('lonely')
		ui, loop = self._init(dungeon, [-1, -1, 'j'])

		self.assertTrue(dungeon.automove())
		self.assertTrue(loop.action())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(loop.action())
		self.assertTrue(dungeon.in_automovement())
		self.assertTrue(loop.action())
		self.assertFalse(dungeon.in_automovement())
	def should_ignore_unknown_keys(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'Z')
		self.assertTrue(loop.action())
	def should_exit(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'S')
		self.assertFalse(loop.action())
	@mock.patch('curses.curs_set')
	def should_enable_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'x')
		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(loop.modes[0].aim, dungeon.scene.get_player().pos)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	@mock.patch('curses.curs_set')
	def should_cancel_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'x')
		loop.modes[0].aim = dungeon.scene.get_player().pos
		ui.cursor(True)
		self.assertTrue(loop.action())
		loop.redraw()
		self.assertIsNone(loop.modes[0].aim)
		curs_set.assert_has_calls([
			mock.call(0),
			])
	@mock.patch('curses.curs_set')
	def should_select_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, '.x.')
		self.assertTrue(loop.action())
		loop.redraw()
		self.assertTrue(loop.action())
		loop.redraw()
		self.assertTrue(loop.action())
		self.assertIsNone(loop.modes[0].aim)
		loop.redraw()
		curs_set.assert_has_calls([
			mock.call(1),
			])
	def should_autoexplore(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'yykko')
		self.assertTrue(loop.action()) # move...
		self.assertTrue(loop.action()) # ...out of...
		self.assertTrue(loop.action()) # ...monster's...
		self.assertTrue(loop.action()) # ...vision
		self.assertTrue(loop.action()) # explore
		self.assertTrue(dungeon.in_automovement())
	def should_toggle_god_settings(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, '~Q~v~c')
		list(dungeon.process_events(raw=True))
		loop.redraw()
		main_display = ui.window.get_calls()
		godmode_display = main_display + [('addstr', 0, 0, 'Select God option (cv)'), ('refresh',)]
		self.maxDiff = None
		self.assertTrue(loop.action()) # ~
		list(dungeon.process_events(raw=True))
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertFalse(loop.action()) # Q
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), main_display)
		self.assertTrue(loop.action()) # ~
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertFalse(loop.action()) # v
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_FULL) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '[vis]'),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
		self.assertTrue(loop.action()) # ~
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_FULL) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '[vis]'),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			('addstr', 0, 0, 'Select God option (cv)'),
			('refresh',),
			])
		self.assertFalse(loop.action()) # c
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_FULL) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '[vis]'),
			('addstr', 24, 39, '[clip]'),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_suicide(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'Q')
		self.assertTrue(loop.action())
		self.assertTrue(dungeon.is_finished())
	def should_descend(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, '>')
		self.assertEqual(next(_ for _ in dungeon.scene.monsters if _.sprite.sprite == 'M').pos, Point(13, 3))
		dungeon.jump_to(dungeon.scene.get_player(), Point(10, 1))
		self.assertTrue(loop.action())
		self.assertNotEqual(next(_ for _ in dungeon.scene.monsters if _.sprite.sprite == 'M').pos, Point(13, 3), msg=dungeon.scene.tostring(Rect((0, 0), dungeon.scene.strata.size)))

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.NEXT_DUNGEON) + [
			('addstr', 0, 0, 'monster! stairs! monster! player V...                                           '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	@mock.patch('curses.curs_set')
	def should_move_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'xhjklyubn')
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(9, 6))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(8, 6))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(8, 7))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(8, 6))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(9, 6))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(8, 5))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(9, 4))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(8, 5))
		self.assertTrue(loop.action())
		self.assertEqual(loop.modes[0].aim, Point(9, 6))
	def should_drop_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		ui, loop = self._init(dungeon, 'd' + chr(Key.ESCAPE) + 'lgdja')

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to drop:',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####        #  ',
				'     ....   #  ...  ',
				'      ...  .# ..... ',
				'     ##..##.#...... ',
				'     #............. ',
				'#.M..#............. ',
				'#........@!........#',
				'#.................. ',
				'#.................. ',
				' #################  ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		self.assertTrue(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'player ^^ potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv:  !'),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to drop:',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		item = dungeon.scene.get_player().inventory[0]
		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'player VV potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, 'here: !'),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_consume_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		ui, loop = self._init(dungeon, 'le' + chr(Key.ESCAPE) + 'gejaeb')

		self.assertTrue(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, 'here: !'),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, 'here: !'),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		dungeon.scene.get_player().grab(mock_dungeon.HealingPotion())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'player ^^ potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv: !!'),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, 'a - potion',),
			('addstr', 2, 0, 'b - healing potion',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, 'a - potion',),
			('addstr', 2, 0, 'b - healing potion',),
			('refresh',),
			])

		item = dungeon.scene.get_player().inventory[0]
		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'X potion.                                                                       '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv: !!'),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, 'a - potion',),
			('addstr', 2, 0, 'b - healing potion',),
			('refresh',),
			])

		item = dungeon.scene.get_player().inventory[1]
		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####      #### ',
				'     ...   ## ..... ',
				'      ...  .#......#',
				'     ##..##.#......#',
				'     #.............#',
				'#    #.............#',
				'#.........@........#',
				'#..................#',
				'#..................#',
				' ################## ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'player <~ healing potion. player+0hp.                                           '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv:  !'),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_drop_loot_from_monsters(self):
		dungeon = mock_dungeon.build('single mock thief')
		ui, loop = self._init(dungeon)
		list(dungeon.process_events(raw=True))

		dungeon.jump_to(dungeon.scene.get_player(), Point(13, 4))
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(self.DISPLAYED_LAYOUT_FIGHT_THIEF) + [
			('addstr', 0, 0, 'player x> thief. thief-1hp.                                                     '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		# Finish him.
		list(dungeon.process_events(raw=True))
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP)
		list(dungeon.process_events(raw=True))
		dungeon.move_actor(dungeon.scene.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		DISPLAYED_LAYOUT_KILLED_MONSTER_WITH_DROP = [
				'    #####   ########',
				'            #......#',
				'            #......#',
				'     ##..##.#$.....#',
				'     #.......@.....#',
				'#    #.............#',
				'#   ...............#',
				'#   ...............#',
				'#   ...............#',
				' ###################',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT_KILLED_MONSTER_WITH_DROP) + [
			('addstr', 0, 0, 'player x> thief. thief-1hp. thief dies. thief VV money. money!                  '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
	def should_show_inventory(self):
		dungeon = mock_dungeon.build('monster and potion')
		ui, loop = self._init(dungeon, 'ia' + chr(Key.ESCAPE) + 'i')
		list(dungeon.process_events(raw=True))

		self.assertTrue(loop.action())
		loop.redraw()

		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####        #  ',
				'     ....   #  ...  ',
				'      ...  .# ..... ',
				'     ##..##.#...... ',
				'     #............. ',
				'#.M..#............. ',
				'#........@!........#',
				'#.................. ',
				'#.................. ',
				' #################  ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		dungeon.move_actor(dungeon.scene.get_player(), Direction.RIGHT)
		dungeon.grab_item_here(dungeon.scene.get_player())

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])
	def should_equip_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		ui, loop = self._init(dungeon, 'E' + chr(Key.ESCAPE) + 'Ea' + chr(Key.ESCAPE) + 'EabaEa')
		dungeon.scene.get_player().inventory.append(mock_dungeon.Weapon())

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		DISPLAYED_LAYOUT = [
				'    #####        #  ',
				'     ....   #  ...  ',
				'      ...  .# ..... ',
				'     ##..##.#...... ',
				'     #............. ',
				'#.M..#............. ',
				'#........@!........#',
				'#.................. ',
				'#.................. ',
				' #################  ',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv:  ('),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to wield:',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv:  ('),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to wield:',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (b)',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'player <+ weapon.                                                               '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, '       '),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - weapon',),
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + self._addstr_map(DISPLAYED_LAYOUT) + [
			('addstr', 0, 0, 'player +> weapon.                                                               '),
			('addstr', 24, 0, 'hp: 10/10  '),
			('addstr', 24, 12, '       '),
			('addstr', 24, 20, 'inv:  ('),
			('addstr', 24, 28, '      '),
			('addstr', 24, 34, '     '),
			('addstr', 24, 39, '      '),
			('addstr', 24, 77, '[?]'),
			('refresh',),
			])
