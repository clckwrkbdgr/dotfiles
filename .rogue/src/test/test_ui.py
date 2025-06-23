import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from .. import ui
from ..ui import MainGame
from .. import items
from .. import defs as _base
from clckwrkbdgr.math import Point, Direction
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

	def should_draw_game(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_show_state_markers(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)
		dungeon.movement_queue = ['mock']

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10 [auto]                                                             [?]'),
			('refresh',),
			])

		dungeon.movement_queue = []
		dungeon.god.vision = True
		dungeon.god.noclip = True

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis] [clip]                                                       [?]'),
			('refresh',),
			])
	def should_display_discover_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, '.')

		dungeon.start_autoexploring()
		# Monster is already spotted from the beginning,
		# now move into cave opening to detect exit.
		dungeon.move(dungeon.get_player(), Direction.UP_RIGHT)
		dungeon.move(dungeon.get_player(), Direction.UP_RIGHT)
		dungeon.move(dungeon.get_player(), Direction.UP_RIGHT)

		dungeon.events.append('GIBBERISH')

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_EXIT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster! monsters! exit! Unknown event {0}!                             '.format(repr('GIBBERISH'))),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT_EXIT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster...                                                                      '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_display_attack_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)
		list(dungeon.process_events(raw=True))

		dungeon.jump_to(Point(13, 4))
		dungeon.move(dungeon.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FIGHT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> monster. monster-1hp.                                                 '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		# Finish him.
		list(dungeon.process_events(raw=True))
		dungeon.move(dungeon.get_player(), Direction.UP)
		dungeon.move(dungeon.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_KILLED_MONSTER[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> monster. monster-1hp. player x> monster. monster-1hp. monster dies.   '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_display_movement_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon)
		list(dungeon.process_events(raw=True))
		dungeon.god.vision = True

		dungeon.move(dungeon.get_player(), Direction.RIGHT)
		dungeon.move(dungeon.get_player(), Direction.RIGHT)
		dungeon.move(dungeon.get_player(), Direction.RIGHT)

		dungeon.move(dungeon.monsters[-1], Direction.LEFT)

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'exit! monster bumps.                                                            '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			])
	def should_wait_user_reaction_after_player_is_dead(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, ' ')
		list(dungeon.process_events(raw=True))

		dungeon.affect_health(dungeon.get_player(), -dungeon.get_player().hp)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_DEAD[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player-10hp. player dies.                                                       '),
			('addstr', 24, 0, '[DEAD] Press Any Key...                                                      [?]'),
			('refresh',),
			])
	def should_perform_dungeon_actions(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'h? q')
		self.assertEqual(loop.action(), True)
		self.assertEqual(dungeon.get_player().pos, Point(8, 6))
		self.assertEqual(loop.action(), True)
		self.assertEqual(loop.action(), False)
		self.assertEqual(loop.action(), False)
	def should_show_keybindings_help(self):
		dungeon = mock_dungeon.build('single mock monster')
		list(dungeon.process_events(raw=True))
		ui, loop = self._init(dungeon, '? ')

		self.assertTrue(loop.action())
		loop.redraw()

		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			] + [('addstr', i, 0, _) for i, _ in enumerate([
			'hjklyubn - Move.',
			'. - Wait.',
			'> - Descend.',
			'? - Show this help.',
			'E - Show equipment.',
			'Q - Suicide (quit without saving).',
			'd - Drop item.',
			'e - Consume item.',
			'g - Grab item.',
			'i - Show inventory.',
			'o - Autoexplore.',
			'q - Save and quit.',
			'x - Examine surroundings (cursor mode).',
			'~ - God mode options.',
			'[Press Any Key...]',
			])] + [
			('refresh',),
			])

		self.assertFalse(loop.action())
		loop.redraw()
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('move', 7, 9),
			('refresh',),
			])
	def should_check_for_user_interrupt(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, [-1, -1, 'j'])

		dungeon.autoexploring = True
		self.assertTrue(loop.action())
		self.assertTrue(dungeon.autoexploring)
		self.assertTrue(loop.action())
		self.assertTrue(dungeon.autoexploring)
		self.assertTrue(loop.action())
		self.assertFalse(dungeon.autoexploring)
	def should_ignore_unknown_keys(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'Z')
		self.assertTrue(loop.action())
	def should_exit(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'q')
		self.assertFalse(loop.action())
	@mock.patch('curses.curs_set')
	def should_enable_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'x')
		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(loop.modes[0].aim, dungeon.get_player().pos)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	@mock.patch('curses.curs_set')
	def should_cancel_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'x')
		loop.modes[0].aim = dungeon.get_player().pos
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
		self.assertTrue(dungeon.autoexploring)
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			])
		self.assertTrue(loop.action()) # ~
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			('addstr', 0, 0, 'Select God option (cv)'),
			('refresh',),
			])
		self.assertFalse(loop.action()) # c
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis] [clip]                                                       [?]'),
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
		dungeon.jump_to(Point(10, 1))
		self.assertTrue(loop.action())

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.NEXT_DUNGEON[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster! exit! player V... monster!                                             '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_move_character(self):
		dungeon = mock_dungeon.build('single mock monster')
		ui, loop = self._init(dungeon, 'hjklyubn')
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(8, 6))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(8, 7))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(8, 6))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(8, 5))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(9, 4))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(8, 5))
		self.assertTrue(loop.action())
		self.assertEqual(dungeon.get_player().pos, Point(9, 6))
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
	def should_grab_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		ui, loop = self._init(dungeon, 'glgD')

		self.assertTrue(loop.action())
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player ^^ potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10 inv:  !                                                            [?]'),
			('refresh',),
			])

		dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
		dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv:  3                                                            [?]'),
			('refresh',),
			])

		for _ in range(10):
			dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv: 13                                                            [?]'),
			('refresh',),
			])
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player ^^ potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10 inv:  !                                                            [?]'),
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

		item = dungeon.get_player().inventory[0]
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player VV potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])
	def should_consume_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		ui, loop = self._init(dungeon, 'le' + chr(Key.ESCAPE) + 'geja')

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player ^^ potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10 inv:  !                                                            [?]'),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
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

		item = dungeon.get_player().inventory[0]
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player <~ potion.                                                               '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_drop_loot_from_monsters(self):
		dungeon = mock_dungeon.build('single mock thief')
		ui, loop = self._init(dungeon)
		list(dungeon.process_events(raw=True))

		dungeon.jump_to(Point(13, 4))
		dungeon.move(dungeon.get_player(), Direction.UP)

		loop.redraw()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FIGHT_THIEF[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> thief. thief-1hp.                                                     '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		# Finish him.
		list(dungeon.process_events(raw=True))
		dungeon.move(dungeon.get_player(), Direction.UP)
		list(dungeon.process_events(raw=True))
		dungeon.move(dungeon.get_player(), Direction.UP)

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT_KILLED_MONSTER_WITH_DROP[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> thief. thief-1hp. thief dies. thief VV money.                         '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		dungeon.move(dungeon.get_player(), Direction.RIGHT)
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))

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
		dungeon.get_player().inventory.append(items.Item(MockGame.ITEMS['weapon'], Point(0, 0)))

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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player <+ weapon.                                                               '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
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
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player +> weapon.                                                               '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])
