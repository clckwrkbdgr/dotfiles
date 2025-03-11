import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
from .. import curses, _base
from ...pcg import builders, settlers
from ... import game, monsters, items, messages, terrain
from ...math import Point
from clckwrkbdgr import utils
from ...test import mock_dungeon
from ...test.mock_dungeon import MockGame

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
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = mock_dungeon.build('single mock monster')

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_show_state_markers(self):
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.movement_queue = ['mock']

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10 [auto]                                                             [?]'),
			('refresh',),
			])

		dungeon.movement_queue = []
		dungeon.god.vision = True
		dungeon.god.noclip = True

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster!                                                                        '),
			('addstr', 24, 0, 'hp: 10/10 [vis] [clip]                                                       [?]'),
			('refresh',),
			])
	def should_display_discover_events(self):
		ui = curses.Curses()
		ui.window = MockCurses('.')
		dungeon = mock_dungeon.build('single mock monster')

		dungeon.start_autoexploring()
		# Monster is already spotted from the beginning,
		# now move into cave opening to detect exit.
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT)
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT)
		dungeon.move(dungeon.get_player(), game.Direction.UP_RIGHT)

		dungeon.events.append('GIBBERISH')

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT_EXIT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster! monsters! exit! Unknown event {0}!                             '.format(repr('GIBBERISH'))),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
		
		dungeon.clear_event()
		self.assertEqual(ui.user_action(dungeon), (_base.Action.WAIT, None))
		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT_EXIT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_display_attack_events(self):
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.clear_event()

		dungeon.jump_to(Point(2, 6))
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
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

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT_KILLED_MONSTER[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> monster. monster-1hp. player x> monster. monster-1hp. monster dies.   '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_display_movement_events(self):
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.clear_event()
		dungeon.god.vision = True

		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.move(dungeon.get_player(), game.Direction.UP)
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		dungeon.move(dungeon.monsters[-1], game.Direction.LEFT)
		dungeon.move(dungeon.monsters[-1], game.Direction.LEFT)

		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT_FULL[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster... monster bumps.                                                       '),
			('addstr', 24, 0, 'hp: 10/10 [vis]                                                              [?]'),
			('refresh',),
			])
	def should_wait_user_reaction_after_player_is_dead(self):
		ui = curses.Curses()
		ui.window = MockCurses(' ')
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.clear_event()

		dungeon.affect_health(dungeon.get_player(), -dungeon.get_player().hp)

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT_DEAD[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player-10hp. player dies.                                                       '),
			('addstr', 24, 0, '[DEAD] Press Any Key...                                                      [?]'),
			('refresh',),
			])
	def should_show_keybindings_help(self):
		ui = curses.Curses()
		ui.window = MockCurses('? ')
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.clear_event()

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)

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

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
	@mock.patch('curses.curs_set')
	def should_display_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('x')
		dungeon = mock_dungeon.build('single mock monster')

		dungeon.clear_event()
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		curs_set.assert_has_calls([
			mock.call(1),
			])

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('move', 7, 9),
			('refresh',),
			])
	def should_check_for_user_interrupt(self):
		ui = curses.Curses()
		ui.window = MockCurses([-1, -1, ' '])
		dungeon = mock_dungeon.build('single mock monster')

		self.assertFalse(ui.user_interrupted())
		self.assertFalse(ui.user_interrupted())
		self.assertTrue(ui.user_interrupted())
	def should_ignore_unknown_keys(self):
		ui = curses.Curses()
		ui.window = MockCurses('Z')
		dungeon = mock_dungeon.build('single mock monster')
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
	def should_exit(self):
		ui = curses.Curses()
		ui.window = MockCurses('q')
		dungeon = mock_dungeon.build('single mock monster')
		self.assertEqual(ui.user_action(dungeon), (_base.Action.EXIT, None))
	@mock.patch('curses.curs_set')
	def should_enable_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('x')
		dungeon = mock_dungeon.build('single mock monster')
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.aim, dungeon.get_player().pos)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	@mock.patch('curses.curs_set')
	def should_cancel_aim(self, curs_set):
		ui = curses.Curses()
		ui.window = MockCurses('x')
		dungeon = mock_dungeon.build('single mock monster')
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
		dungeon = mock_dungeon.build('single mock monster')
		self.assertEqual(ui.user_action(dungeon), (_base.Action.WAIT, None))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.WALK_TO, Point(9, 6)))
		self.assertIsNone(ui.aim)
		curs_set.assert_has_calls([
			mock.call(1),
			])
	def should_autoexplore(self):
		ui = curses.Curses()
		ui.window = MockCurses('o')
		dungeon = mock_dungeon.build('single mock monster')
		self.assertEqual(ui.user_action(dungeon), (_base.Action.AUTOEXPLORE, None))
	def should_toggle_god_settings(self):
		ui = curses.Curses()
		ui.window = MockCurses('~Q~v~c')
		dungeon = mock_dungeon.build('single mock monster')
		ui.redraw(dungeon)
		main_display = ui.window.get_calls()
		godmode_display = main_display + [('addstr', 0, 0, 'Select God option (cv)'), ('refresh',)]
		self.maxDiff = None
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), main_display)
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertEqual(ui.user_action(dungeon), (_base.Action.GOD_TOGGLE_VISION, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), main_display)
		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), godmode_display)
		self.assertEqual(ui.user_action(dungeon), (_base.Action.GOD_TOGGLE_NOCLIP, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), main_display)
	def should_suicide(self):
		ui = curses.Curses()
		ui.window = MockCurses('Q')
		dungeon = mock_dungeon.build('single mock monster')
		self.assertEqual(ui.user_action(dungeon), (_base.Action.SUICIDE, None))
	def should_descend(self):
		ui = curses.Curses()
		ui.window = MockCurses('>')
		dungeon = mock_dungeon.build('single mock monster')
		dungeon.jump_to(Point(10, 1))
		self.assertEqual(ui.user_action(dungeon), (_base.Action.DESCEND, None))
		dungeon.descend()

		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, self.NEXT_DUNGEON[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'monster! exit! player V... monster!                                             '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_move_character(self):
		ui = curses.Curses()
		ui.window = MockCurses('hjklyubn')
		dungeon = mock_dungeon.build('single mock monster')
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
		dungeon = mock_dungeon.build('single mock monster')
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
	def should_grab_items(self):
		self.maxDiff = None
		ui = curses.Curses()
		ui.window = MockCurses('glgD')
		dungeon = mock_dungeon.build('monster and potion')

		self.assertEqual(ui.user_action(dungeon), (_base.Action.GRAB, Point(9, 6)))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.RIGHT))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.GRAB, Point(10, 6)))
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion.                                              '),
			('addstr', 24, 0, 'hp: 10/10 inv:  !                                                            [?]'),
			('refresh',),
			])

		dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
		dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion.                                              '),
			('addstr', 24, 0, 'hp: 10/10 inv:  3                                                            [?]'),
			('refresh',),
			])

		for _ in range(10):
			dungeon.get_player().inventory.append(dungeon.get_player().inventory[0])
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion.                                              '),
			('addstr', 24, 0, 'hp: 10/10 inv: 13                                                            [?]'),
			('refresh',),
			])
	def should_drop_items(self):
		self.maxDiff = None
		ui = curses.Curses()
		ui.window = MockCurses('d' + curses.Keymapping.ESC + 'lgdja')
		dungeon = mock_dungeon.build('monster and potion')

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to drop:',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.RIGHT))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		self.assertEqual(ui.user_action(dungeon), (_base.Action.GRAB, Point(10, 6)))
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion.                                              '),
			('addstr', 24, 0, 'hp: 10/10 inv:  !                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to drop:',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.DROP, dungeon.get_player().inventory[0]))
		dungeon.drop_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion. player VV potion.                            '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])
	def should_consume_items(self):
		self.maxDiff = None
		ui = curses.Curses()
		ui.window = MockCurses('le' + curses.Keymapping.ESC + 'geja')
		dungeon = mock_dungeon.build('monster and potion')

		self.assertEqual(ui.user_action(dungeon), (_base.Action.MOVE, game.Direction.RIGHT))
		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 here: !                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.GRAB, Point(10, 6)))
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion.                                              '),
			('addstr', 24, 0, 'hp: 10/10 inv:  !                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to consume:',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.CONSUME, dungeon.get_player().inventory[0]))
		dungeon.consume_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player ^^ potion. player <~ potion.                            '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_drop_loot_from_monsters(self):
		ui = curses.Curses()
		ui.window = MockCurses()
		dungeon = mock_dungeon.build('single mock thief')
		dungeon.clear_event()

		dungeon.jump_to(Point(2, 6))
		dungeon.move(dungeon.get_player(), game.Direction.UP)

		ui.redraw(dungeon)
		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
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

		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT_KILLED_MONSTER_WITH_DROP[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'player x> thief. thief-1hp. thief dies. thief VV money.                         '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])
	def should_show_inventory(self):
		ui = curses.Curses()
		ui.window = MockCurses('ia' + curses.Keymapping.ESC + 'i')
		dungeon = mock_dungeon.build('monster and potion')
		dungeon.clear_event()

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)

		self.maxDiff = None
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, '(Empty)',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, '                                                                                '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		dungeon.move(dungeon.get_player(), game.Direction.RIGHT)
		dungeon.grab_item_at(dungeon.get_player(), Point(10, 6))

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 1, 0, 'a - potion',),
			('refresh',),
			])
	def should_equip_items(self):
		self.maxDiff = None
		ui = curses.Curses()
		ui.window = MockCurses('E' + curses.Keymapping.ESC + 'Ea' + curses.Keymapping.ESC + 'EabaEa')
		dungeon = mock_dungeon.build('monster and potion')
		dungeon.get_player().inventory.append(items.Item(MockGame.ITEMS['weapon'], Point(0, 0)))

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
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
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to wield:',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster!                                                                '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - None',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'Select item to wield:',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (b)',),
			('addstr', 1, 0, 'a - weapon',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.WIELD, dungeon.get_player().inventory[0]))
		dungeon.wield_item(dungeon.get_player(), dungeon.get_player().inventory[0])
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player <+ weapon.                                              '),
			('addstr', 24, 0, 'hp: 10/10                                                                    [?]'),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.NONE, None))
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'wielding [a] - weapon',),
			('refresh',),
			])

		self.assertEqual(ui.user_action(dungeon), (_base.Action.UNWIELD, None))
		dungeon.unwield_item(dungeon.get_player())
		ui.redraw(dungeon)
		self.assertEqual(ui.window.get_calls(), [
			('addstr', y, x, DISPLAYED_LAYOUT[y-1][x]) for y in range(1, 11) for x in range(20)
			] + [
			('addstr', 0, 0, 'potion! monster! player <+ weapon. player +> weapon.                            '),
			('addstr', 24, 0, 'hp: 10/10 inv:  (                                                            [?]'),
			('refresh',),
			])
