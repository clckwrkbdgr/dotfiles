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
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '!',),
			('addstr', 1, 6, '- potion',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '!',),
			('addstr', 1, 6, '- potion',),
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
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '!',),
			('addstr', 1, 6, '- potion',),
			('addstr', 2, 0, '[b] ',),
			('addstr', 2, 4, '!',),
			('addstr', 2, 6, '- healing potion',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (j)',),
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '!',),
			('addstr', 1, 6, '- potion',),
			('addstr', 2, 0, '[b] ',),
			('addstr', 2, 4, '!',),
			('addstr', 2, 6, '- healing potion',),
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
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '!',),
			('addstr', 1, 6, '- potion',),
			('addstr', 2, 0, '[b] ',),
			('addstr', 2, 4, '!',),
			('addstr', 2, 6, '- healing potion',),
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
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '(',),
			('addstr', 1, 6, '- weapon',),
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
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '(',),
			('addstr', 1, 6, '- weapon',),
			('refresh',),
			])

		self.assertTrue(loop.action())
		loop.redraw()
		self.assertEqual(ui.window.get_calls(), [
			('clear',),
			('addstr', 0, 0, 'No such item (b)',),
			('addstr', 1, 0, '[a] ',),
			('addstr', 1, 4, '(',),
			('addstr', 1, 6, '- weapon',),
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
