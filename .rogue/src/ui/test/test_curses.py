import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from .. import curses, _base
from ..curses import MainGame
from ...pcg import builders, settlers
from ... import game, monsters, items, messages, terrain
from clckwrkbdgr.math import Point
from clckwrkbdgr import utils
from ...test import mock_dungeon
from ...test.mock_dungeon import MockGame
from clckwrkbdgr.tui import Key

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
			'     ##..##.#...... ',
			'     #............. ',
			'#.M..#............. ',
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
			'#....#............. ',
			'#........@.........#',
			'#.................. ',
			'#......M........... ',
			' #################  ',
			]
	DISPLAYED_LAYOUT_DEAD = [
			'    #####        #  ',
			'     ....   #  ...  ',
			'      ...  .# ..... ',
			'     ##..##.#...... ',
			'     #............. ',
			'#.M..#............. ',
			'#..................#',
			'#.................. ',
			'#.................. ',
			' #################  ',
			]
	DISPLAYED_LAYOUT_EXIT = [
			'  #########      ###',
			'          >##    ..#',
			'          ..#  ....#',
			'     ##..##.#......#',
			'     #.....@.......#',
			'#    #.............#',
			'#  ................#',
			'# .................#',
			'# .................#',
			' ###################',
			]
	DISPLAYED_LAYOUT_FIGHT = [
			'#########        #  ',
			'#......     #       ',
			'#.....      #       ',
			'#....##  ## #       ',
			'#....#              ',
			'#.M..#......        ',
			'#.@..........      #',
			'#...........        ',
			'#...........        ',
			'##################  ',
			]
	DISPLAYED_LAYOUT_FIGHT_THIEF = [
			'#########        #  ',
			'#......     #       ',
			'#.....      #       ',
			'#....##  ## #       ',
			'#....#              ',
			'#.T..#......        ',
			'#.@..........      #',
			'#...........        ',
			'#...........        ',
			'##################  ',
			]
	DISPLAYED_LAYOUT_KILLED_MONSTER = [
			'#########        #  ',
			'#......     #       ',
			'#.....      #       ',
			'#....##  ## #       ',
			'#....#              ',
			'#....#......        ',
			'#.@..........      #',
			'#...........        ',
			'#...........        ',
			'##################  ',
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

	def should_handle_all_events(self):
		handled_events = curses.Events.list_all_events()
		known_events = sorted(utils.all_subclasses(messages.Event), key=lambda cls: cls.__name__)
		self.assertEqual(known_events, handled_events)

	def should_draw_game(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses()

		ui.redraw_all()
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses()
		dungeon.movement_queue = ['mock']

		ui.redraw_all()
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

		ui.redraw_all()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10 [vis] [clip]                                                       [?]'),
			('refresh',),
			])
	def should_display_discover_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('.')

		dungeon.start_autoexploring()
		# Monster is already spotted from the beginning,
		# now move into cave opening to detect exit.
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT)
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT)
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT)

		dungeon.events.append('GIBBERISH')

		ui.redraw_all()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_EXIT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster! monsters! exit! Unknown event {0}!                             '.format(repr('GIBBERISH'))),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
		
		dungeon.clear_event()
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.WAIT, None))
		ui.redraw_all()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_EXIT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_display_attack_events(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses()
		dungeon.clear_event()

		dungeon.jump_to(Point(2, 6))
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		ui.redraw_all()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FIGHT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> monster. monster-1hp.                                                 '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		# Finish him.
		dungeon.clear_event()
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		ui.redraw_all()
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses()
		dungeon.clear_event()
		dungeon.god.vision = True

		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		dungeon.move(dungeon.monsters[-1], game.Direction.LEFT)
		dungeon.move(dungeon.monsters[-1], game.Direction.LEFT)

		ui.redraw_all()
		self.maxDiff = None
		DISPLAYED_LAYOUT_FULL = [
				'####################',
				'#........#>##......#',
				'#........#..#......#',
				'#....##..##.#......#',
				'#....#...@.........#',
				'#M...#.............#',
				'#..................#',
				'#..................#',
				'#..................#',
				'####################',
				]
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster... monster bumps.                                                       '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			])
	def should_wait_user_reaction_after_player_is_dead(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses(' ')
		dungeon.clear_event()

		dungeon.affect_health(dungeon.get_player(), -dungeon.get_player().hp)

		ui.redraw_all()
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('h? q')
		self.assertEqual(ui.pre_action(), True)
		self.assertEqual(ui.action(), True)
		self.assertEqual(dungeon.get_player().pos, Point(8, 6))
		self.assertEqual(ui.pre_action(), True)
		self.assertEqual(ui.action(), True)
		self.assertEqual(ui.pre_action(), True)
		self.assertEqual(ui.action(), True)
		self.assertEqual(ui.pre_action(), True)
		self.assertEqual(ui.action(), False)
	def should_show_keybindings_help(self):
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.clear_event()
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('? ')

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()

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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
	@mock.patch('curses.curs_set')
	def should_display_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('x')

		dungeon.clear_event()
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		curs_set.assert_has_calls([
			mock.call(1),
			])

		ui.redraw_all()
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses([-1, -1, 'j'])

		dungeon.autoexploring = True
		self.assertTrue(ui.pre_action())
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertTrue(ui.pre_action())
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertTrue(ui.pre_action())
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.AUTOSTOP, None))
	def should_ignore_unknown_keys(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('Z')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
	def should_exit(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('q')
		self.assertFalse(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.EXIT, None))
	@mock.patch('curses.curs_set')
	def should_enable_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('x')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, dungeon.get_player().pos)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	@mock.patch('curses.curs_set')
	def should_cancel_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('x')
		ui.loop.modes[0].aim = dungeon.get_player().pos
		ui.cursor(True)
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertIsNone(ui.loop.modes[0].aim)
		curs_set.assert_has_calls([
			mock.call(0),
			])
	@mock.patch('curses.curs_set')
	def should_select_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('.x.')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.WAIT, None))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.WALK_TO, Point(9, 6)))
		self.assertIsNone(ui.loop.modes[0].aim)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	def should_autoexplore(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('o')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.AUTOEXPLORE, None))
	def should_toggle_god_settings(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('~Q~v~c')
		dungeon.clear_event()
		ui.redraw_all()
		main_display = ui.window.get_calls()
		godmode_display = main_display + [('addstr', 0, 0, 'Select God option (cv)'), ('refresh',)]
		self.maxDiff = None
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		dungeon.clear_event()
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), main_display)
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.GOD_TOGGLE_VISION, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			])
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			('addstr', 0, 0, 'Select God option (cv)'),
			('refresh',),
			])
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.GOD_TOGGLE_NOCLIP, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 [vis] [clip]                                                       [?]'),
			('refresh',),
			])
	def should_suicide(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('Q')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.SUICIDE, None))
	def should_descend(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('>')
		dungeon.jump_to(Point(10, 1))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.DESCEND, None))
		dungeon.descend()

		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.NEXT_DUNGEON[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player V... monster!                                                            '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_move_character(self):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('hjklyubn')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.LEFT))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.DOWN))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.UP))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.RIGHT))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.UP_LEFT))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.UP_RIGHT))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.DOWN_LEFT))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.DOWN_RIGHT))
	@mock.patch('curses.curs_set')
	def should_move_aim(self, curs_set):
		dungeon = mock_dungeon.build('single mock monster')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('xhjklyubn')
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(9, 6))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(8, 6))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(8, 7))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(8, 6))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(9, 6))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(8, 5))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(9, 4))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(8, 5))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		self.assertEqual(ui.loop.modes[0].aim, Point(9, 6))
	def should_grab_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('glgD')

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.GRAB, Point(9, 6)))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.RIGHT))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.GRAB, Point(10, 6)))
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		ui.redraw_all()
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
		ui.redraw_all()
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
			('addstr', 24, 0, 'hp: 10/10 inv:  3                                                            [?]'),
			('refresh',),
			])

		for _ in range(10):
			dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
		ui.redraw_all()
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
			('addstr', 24, 0, 'hp: 10/10 inv: 13                                                            [?]'),
			('refresh',),
			])
	def should_drop_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('d' + chr(Key.ESCAPE) + 'lgdja')

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to drop:',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.RIGHT))
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.GRAB, Point(10, 6)))
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to drop:',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		item = dungeon.get_player().inventory[0]
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.DROP, item))
		ui.redraw_all()
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('le' + chr(Key.ESCAPE) + 'geja')

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.MOVE, game.Direction.RIGHT))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.GRAB, Point(10, 6)))
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		ui.redraw_all()
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

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		item = dungeon.get_player().inventory[0]
		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.CONSUME, item))
		ui.redraw_all()
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses()
		dungeon.clear_event()

		dungeon.jump_to(Point(2, 6))
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		ui.redraw_all()
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FIGHT_THIEF[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> thief. thief-1hp.                                                     '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		# Finish him.
		dungeon.clear_event()
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.clear_event()
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		ui.redraw_all()
		self.maxDiff = None
		DISPLAYED_LAYOUT_KILLED_MONSTER_WITH_DROP = [
				'#########        #  ',
				'#......     #       ',
				'#.....      #       ',
				'#....##  ## #       ',
				'#....#              ',
				'#.$..#......        ',
				'#.@..........      #',
				'#...........        ',
				'#...........        ',
				'##################  ',
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
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('ia' + chr(Key.ESCAPE) + 'i')
		dungeon.clear_event()

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()

		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
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

		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])
	def should_equip_items(self):
		self.maxDiff = None
		dungeon = mock_dungeon.build('monster and potion')
		main_mode = MainGame(dungeon)
		ui = curses.Curses(main_mode)
		ui.window = MockCurses('E' + chr(Key.ESCAPE) + 'Ea' + chr(Key.ESCAPE) + 'EabaEa')
		dungeon.get_player().inventory.append(items.Item(MockGame.ITEMS['weapon'], Point(0, 0)))

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
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
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to wield:',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to wield:',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (b)',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.WIELD, dungeon.get_player().wielding))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player <+ weapon.                                                               '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.NONE, None))
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - weapon',),
			('refresh',),
			])

		self.assertTrue(ui.action())
		self.assertEqual(ui.last_result, (_base.Action.UNWIELD, None))
		dungeon.unwield_item(dungeon.get_player())
		ui.redraw_all()
		self.assertEqual(ui.window.get_calls(), [('clear',)] + [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player +> weapon.                                                               '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])
