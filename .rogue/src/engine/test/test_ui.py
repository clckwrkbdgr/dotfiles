from clckwrkbdgr import unittest
import contextlib
from clckwrkbdgr.math.grid import Matrix
from clckwrkbdgr.math import Point, Size, Rect
import clckwrkbdgr.tui
from .. import ui
from .. import Game, Events
from clckwrkbdgr.pcg import RNG
from ..mock import *

class MockUI:
	class MockCurses(clckwrkbdgr.tui.Curses):
		""" FIXME: Needed only for Curses.get_control implementation,
		which depends on get_keypress implementation.
		"""
		def __init__(self, mock_ui):
			super(MockUI.MockCurses, self).__init__()
			self._mock_ui = mock_ui
		def get_keypress(self, *args, **kwargs):
			return self._mock_ui.get_keypress(*args, **kwargs)
	def __init__(self):
		self.screen = Matrix((30, 7), ' ')
		self._cursor = None
		self._mock_curses = self.MockCurses(self)
		self._keys = []
	@contextlib.contextmanager
	def redraw(self, clean=False):
		if clean:
			self.screen.clear(' ')
		yield self
	def print_char(self, x, y, sprite, color):
		self.screen.set_cell((x, y), sprite)
	def print_line(self, y, x, line, color=None):
		for i, c in enumerate(line):
			p = Point(x + i, y)
			if self.screen.valid(p):
				self.screen.set_cell(p, c)
	def cursor(self, value=None):
		if value is True:
			self._cursor = Point(0, 0)
		elif value is False:
			self._cursor = None
		else:
			return self
	def move(self, x, y):
		self._cursor = Point(x, y)
	def get_keypress(self, nodelay=False, timeout=None):
		value = self._keys.pop(0)
		return value
	# Internal.
	def key(self, key_chars):
		for key_char in key_chars:
			self._keys.append(clckwrkbdgr.tui.Key(key_char))
	def get_control(self, *args, **kwargs):
		result = self._mock_curses.get_control(*args, **kwargs)
		return result

class MockMainGame(ui.MainGame):
	INDICATORS = [
			ui.Indicator((0, 0), 10, lambda _:'pos: {0}'.format(_.game.scene.get_player().pos)),
			ui.Indicator((12, 0), 10, lambda _:'aim: {0}'.format(_.aim) if _.aim else ''),
			ui.Indicator((9, 1), 10, lambda _:'monsters: {0}'.format(len(_.game.scene.monsters))),
			]
	def get_map_shift(self):
		return Point(0, 1)
	def get_message_line_rect(self):
		return Rect(Point(0, 6), Size(27, 1))
	def get_viewrect(self):
		return Rect(
				self.game.scene.get_player().pos - Point(2, 2),
				Size(5, 5),
				)

class MainGameTestCase(unittest.TestCase):
	def setUp(self):
		self.maxDiff = None
		self.game = NanoDungeon(RNG(0))
		self.game.generate(None)
		self.mode = MockMainGame(self.game)
		self.mock_ui = MockUI()
		self.loop = clckwrkbdgr.tui.ModeLoop(self.mock_ui)
		self.loop.modes.append(self.mode)
	def tearDown(self):
		self.assertFalse(self.mock_ui._keys, msg="Not all keys were used up.")

class TestMainGameDisplay(MainGameTestCase):
	def should_get_visible_sprites(self):
		mode, mock_ui = self.mode, self.mock_ui
		mode.game.update_vision()
		self.assertEqual(mode.get_sprite(Point(0, 5)), ui.Sprite('#', None))
		self.assertEqual(mode.get_sprite(Point(1, 5)), ui.Sprite('@', None))
		mode.game.scene.get_player().pos = Point(1, 1)
		mode.game.update_vision()
		self.assertEqual(mode.get_sprite(Point(3, 2)), ui.Sprite('&', None))
		self.assertEqual(mode.get_sprite(Point(1, 2)), ui.Sprite('?', None))
	def should_get_remembered_sprites(self):
		mode, mock_ui = self.mode, self.mock_ui
		mode.game.scene.get_player().pos = Point(1, 1)
		mode.game.update_vision()
		mode.game.scene.get_player().pos = Point(7, 7)
		mode.game.update_vision()
		self.assertEqual(mode.get_sprite(Point(3, 2)), ui.Sprite('&', None))
		self.assertEqual(mode.get_sprite(Point(1, 2)), None) # ?
		self.assertEqual(mode.get_sprite(Point(0, 0)), ui.Sprite('#', None))
	def should_draw_map(self):
		mode, mock_ui = self.mode, self.mock_ui

		# To display some void south of the wall:
		mode.game.scene.get_player().pos = Point(4, 8)
		mode.game.update_vision()

		mode.draw_map(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_                              _
		_.~>..                         _
		_.....                         _
		_.b@..                         _
		_#####                         _
		_                              _
		_                              _
		""").replace('_', ''))
	def should_print_messages(self):
		mode, mock_ui = self.mode, self.mock_ui
		mode.messages = [
		'Hello, this is the first message and it is long.'
		'Second, also long.',
		'Third.',
		'Last.',
		]

		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"Hello, this is the fir[...]   \n"
			]))
		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"st message and it is l[...]   \n"
			]))
		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"ong.Second, also long.[...]   \n"
			]))
		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"Third. Last.                  \n"
			]))
		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"                              \n"
			]))
	def should_draw_status(self):
		mode, mock_ui = self.mode, self.mock_ui
		mode.draw_status(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [1, 5]                   _
		_         monsters: 2          _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
	def should_show_cursor(self):
		mode, mock_ui = self.mode, self.mock_ui
		mode.aim = Point(3, 3)
		mode.redraw(mock_ui)
		self.assertEqual(mock_ui._cursor, Point(4, 1))
	def should_draw_everything(self):
		mode, mock_ui = self.mode, self.mock_ui
		mode.messages = [
		'Hello, this is the first message and it is long.'
		'Second, also long...',
		'Third.',
		'Last.',
		]
		mode.game.scene.get_player().pos = Point(4, 7)
		mode.game.update_vision()
		mode.redraw(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [4, 7]                   _
		_.....    monsters: 2          _
		_.~>..                         _
		_..@..                         _
		_.b...                         _
		_#####                         _
		_Hello, this is the fir[...]   _
		""").replace('_', ''))

class TestMainGameCustomizations(MainGameTestCase):
	def should_disable_keymapping_when_player_does_not_control(self):
		mode, mock_ui = self.mode, self.mock_ui
		self.assertIsNotNone(mode.get_keymapping())

		mode.messages.append('mock message')
		self.assertIsNone(mode.get_keymapping())
		mode.messages = []

		mode.game.automovement = True
		self.assertIsNone(mode.get_keymapping())
		mode.game.automovement = False

		mode.game.scene.get_player().hp = 0
		self.assertIsNone(mode.get_keymapping())
	def should_perform_pre_action_checks(self):
		mode, mock_ui = self.mode, self.mock_ui
		self.assertTrue(mode.pre_action())
		mode.game.scene.monsters.remove(mode.game.scene.get_player())
		self.assertFalse(mode.pre_action())
	def should_perform_post_actions(self):
		mode, mock_ui = self.mode, self.mock_ui
		self.assertTrue(mode.action(False))
		self.assertFalse(mode.action(True))

		mode.messages.append('mock message')
		self.assertTrue(mode.action(clckwrkbdgr.tui.Key(' ')))
		mode.messages = []

		mode.game.scene.monsters.remove(mode.game.scene.get_player())
		self.assertFalse(mode.action(clckwrkbdgr.tui.Key(' ')))

class TestMainGameControls(MainGameTestCase):
	def should_quit_game_and_save(self):
		self.mock_ui.key('S')
		self.assertFalse(self.loop.action())
		self.assertTrue(self.game.scene.get_player())
	def should_abandon_game(self):
		self.mock_ui.key('Q')
		self.assertTrue(self.loop.action())
		self.assertFalse(self.game.scene.get_player())
	def should_start_and_stopautoexplore(self):
		self.mock_ui.key('o.')
		self.assertFalse(self.game.automovement)
		self.assertTrue(self.loop.action())
		self.assertTrue(self.game.automovement)
		self.assertTrue(self.loop.action())
		self.assertFalse(self.game.automovement)
	def should_wait_in_place(self):
		self.mock_ui.key('.')
		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.playing_time, 1)
	def should_move(self):
		self.mock_ui.key('lb')
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.game.update_vision()
		self.mode.draw_map(self.mock_ui)
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_                              _
		_#....                         _
		_#....                         _
		_#<@..                         _
		_##.~>                         _
		_#....                         _
		_                              _
		""").replace('_', ''))
	def should_grab_item(self):
		self.mock_ui.key('kkkg')
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.game.scene.get_player().find_item(ScribbledNote))
	def should_descend_and_ascend(self):
		self.mock_ui.key('><')
		self.game.jump_to(self.game.scene.get_player(), Point(4, 6))
		self.game.scene.get_player().grab(Gold())

		self.assertTrue(self.loop.action())
		self.mode.draw_map(self.mock_ui)
		self.assertEqual(self.game.current_scene_id, 'tomb')
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_                              _
		_                              _
		_ ###                          _
		_ #@##                         _
		_ #...                         _
		_ ####                         _
		_                              _
		""").replace('_', ''))

		self.assertTrue(self.loop.action())
		self.mode.draw_map(self.mock_ui)
		self.assertEqual(self.game.current_scene_id, 'floor')
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_                              _
		_.....                         _
		_.....                         _
		_..@..                         _
		_~....                         _
		_.....                         _
		_                              _
		""").replace('_', ''))

class TestAim(MainGameTestCase):
	def should_start_aim_mode(self):
		self.mock_ui.key('x')
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui._cursor, Point(2, 3))
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [1, 5] aim: [1, 5]       _
		_ #...    monsters: 2          _
		_ #...                         _
		_ #@..                         _
		_ ##.~                         _
		_ #...                         _
		_                              _
		""").replace('_', ''))
	def should_cancel_aim_mode(self):
		self.mock_ui.key('xlx')
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertIsNone(self.mock_ui._cursor)
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [1, 5]                   _
		_ #...    monsters: 2          _
		_ #...                         _
		_ #@..                         _
		_ ##.~                         _
		_ #...                         _
		_                              _
		""").replace('_', ''))
	def should_move_aim(self):
		self.mock_ui.key('xnlj')
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui._cursor, Point(4, 5))
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [1, 5] aim: [3, 7]       _
		_ #...    monsters: 2          _
		_ #...                         _
		_ #@..                         _
		_ ##.~                         _
		_ #...                         _
		_                              _
		""").replace('_', ''))
	def should_select_aim(self):
		self.mock_ui.key('xnlj.')
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertIsNone(self.mock_ui._cursor)
		self.assertTrue(self.game.automovement)
		self.assertEqual(self.game.automovement.dest, Point(3, 7))
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [1, 5]                   _
		_ #...    monsters: 2          _
		_ #...                         _
		_ #@..                         _
		_ ##.~                         _
		_ #...                         _
		_                              _
		""").replace('_', ''))

class TestHelpScreen(MainGameTestCase):
	def should_show_help_info(self):
		self.mock_ui.key('? ')
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		hjklyubn - Move around.       _
		. - Wait in-place / go to sele_
		< - Ascend/go up.             _
		> - Descend/go down.          _
		? - Show this help.           _
		E - Show equipment.           _
		Q - Suicide (quit without savi_
		""").replace('_', ''))
		self.assertFalse(self.loop.action())

class TestGodModes(MainGameTestCase):
	def should_show_god_mode_state(self):
		self.mock_ui.key('~~')
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select God option:            _
		_c - [ ] - Walk through walls. _
		_v - [ ] - See all.            _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action())
	def should_display_enabled_god_mode(self):
		self.mock_ui.key('~')
		self.game.god.toggle_vision()
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select God option:            _
		_c - [ ] - Walk through walls. _
		_v - [X] - See all.            _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
	def should_toggle_god_vision(self):
		self.mock_ui.key('~v')
		self.assertTrue(self.loop.action())
		self.assertFalse(self.loop.action())
		self.assertTrue(self.game.god.vision)
	def should_toggle_god_noclip(self):
		self.mock_ui.key('~c')
		self.assertTrue(self.loop.action())
		self.assertFalse(self.loop.action())
		self.assertTrue(self.game.god.noclip)

class TestInventory(MainGameTestCase):
	def should_show_inventory(self):
		self.mock_ui.key('ii')
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Inventory:                    _
		_[a] ( - dagger                _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action())
	def should_show_empty_inventory(self):
		self.mock_ui.key('i' + chr(clckwrkbdgr.tui.Key.ESCAPE))
		self.game.scene.get_player().drop(
				self.game.scene.get_player().inventory[0]
				)
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Inventory:                    _
		_(Empty)                       _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action())
	def should_accumulate_items_with_same_name(self):
		self.mock_ui.key('i' + chr(clckwrkbdgr.tui.Key.ESCAPE))
		self.game.scene.get_player().grab(Dagger())
		self.game.scene.get_player().grab(Gold())
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Inventory:                    _
		_[a] ( - dagger (x2)           _
		_[c] * - gold                  _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action())
	def should_warn_about_invalid_item_selection(self):
		self.mock_ui.key('dz')
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to drop:          _
		_[a] ( - dagger                _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))

		self.assertTrue(self.loop.action())
		self.assertTrue(self.game.scene.get_player().inventory)
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_No such item (z)              _
		_[a] ( - dagger                _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
	def should_drop_from_inventory(self):
		self.mock_ui.key('da')
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to drop:          _
		_[a] ( - dagger                _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))

		self.assertFalse(self.loop.action())
		self.assertFalse(self.game.scene.get_player().inventory)
	def should_cancel_action_from_inventory(self):
		self.mock_ui.key('d' + chr(clckwrkbdgr.tui.Key.ESCAPE))
		self.assertTrue(self.loop.action())
		self.assertFalse(self.loop.action())
		self.assertTrue(self.game.scene.get_player().inventory)
	def should_not_drop_when_inventory_is_empty(self):
		self.mock_ui.key('d')
		self.game.scene.get_player().drop(
				self.game.scene.get_player().inventory[0]
				)
		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.events, [
			Events.Welcome(),
			Events.InventoryIsEmpty(),
			])
	def should_consume_items(self):
		self.mock_ui.key('eab')
		self.game.scene.get_player().grab(Potion())
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to consume:       _
		_[a] ( - dagger                _
		_[b] ! - potion                _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))

		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.events, [
			Events.Welcome(),
			Events.NotConsumable(self.game.scene.get_player().inventory[0]),
			])
		self.assertEqual(len(self.game.scene.get_player().inventory), 2)

		list(self.game.process_events(raw=True))
		self.assertFalse(self.loop.action())
		self.assertEqual(len(self.game.scene.get_player().inventory), 1)
	def should_not_consume_when_inventory_is_empty(self):
		self.mock_ui.key('e')
		self.game.scene.get_player().drop(
				self.game.scene.get_player().inventory[0]
				)
		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.events, [
			Events.Welcome(),
			Events.InventoryIsEmpty(),
			])
	def should_wield_and_unwield_items(self):
		self.mock_ui.key('waU')
		list(self.game.process_events(raw=True))
		dagger = self.game.scene.get_player().inventory[0]
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to wield:         _
		_[a] ( - dagger                _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))

		self.assertFalse(self.loop.action())
		self.assertFalse(self.game.scene.get_player().inventory)
		self.assertEqual(self.game.scene.get_player().wielding, dagger)

		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.scene.get_player().inventory, [dagger])
		self.assertIsNone(self.game.scene.get_player().wielding)
	def should_not_wield_when_inventory_is_empty(self):
		self.mock_ui.key('w')
		self.game.scene.get_player().drop(
				self.game.scene.get_player().inventory[0]
				)
		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.events, [
			Events.Welcome(),
			Events.InventoryIsEmpty(),
			])
	def should_wear_and_take_off_items(self):
		self.mock_ui.key('WabT')
		self.game.scene.get_player().grab(Rags())
		list(self.game.process_events(raw=True))
		dagger = self.game.scene.get_player().inventory[0]
		rags = self.game.scene.get_player().inventory[1]
		self.assertTrue(self.loop.action())
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to wear:          _
		_[a] ( - dagger                _
		_[b] [ - rags                  _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))

		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.events, [
			Events.NotWearable(dagger),
			])
		self.assertEqual(len(self.game.scene.get_player().inventory), 2)

		list(self.game.process_events(raw=True))
		self.assertFalse(self.loop.action())
		self.assertEqual(self.game.scene.get_player().inventory, [dagger])
		self.assertEqual(self.game.scene.get_player().wearing, rags)

		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.scene.get_player().inventory, [dagger, rags])
		self.assertIsNone(self.game.scene.get_player().wearing)
	def should_not_wear_when_inventory_is_empty(self):
		self.mock_ui.key('W')
		self.game.scene.get_player().drop(
				self.game.scene.get_player().inventory[0]
				)
		self.assertTrue(self.loop.action())
		self.assertEqual(self.game.events, [
			Events.Welcome(),
			Events.InventoryIsEmpty(),
			])
	def should_equip_items_via_equipment_screen(self):
		self.mock_ui.key('E' + chr(clckwrkbdgr.tui.Key.ESCAPE) + 'EaaEaEbaEb')
		dagger = self.game.scene.get_player().inventory[0]
		rags = Rags()
		self.game.scene.get_player().grab(rags)
		list(self.game.process_events(raw=True))

		self.assertTrue(self.loop.action()) # E
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_wielding [a] - None           _
		_wearing  [b] - None           _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # ESC

		self.assertTrue(self.loop.action()) # E
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_wielding [a] - None           _
		_wearing  [b] - None           _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # a
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to wield:         _
		_[a] ( - dagger                _
		_[b] [ - rags                  _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # a
		self.assertEqual(self.game.scene.get_player().inventory, [rags])
		self.assertEqual(self.game.scene.get_player().wielding, dagger)

		self.assertTrue(self.loop.action()) # E
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_wielding [a] - dagger         _
		_wearing  [b] - None           _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # a
		self.assertEqual(self.game.scene.get_player().inventory, [rags, dagger])
		self.assertIsNone(self.game.scene.get_player().wielding)

		self.assertTrue(self.loop.action()) # E
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_wielding [a] - None           _
		_wearing  [b] - None           _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # b
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_Select item to wear:          _
		_[a] [ - rags                  _
		_[b] ( - dagger                _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # a
		self.assertEqual(self.game.scene.get_player().inventory, [dagger])
		self.assertEqual(self.game.scene.get_player().wearing, rags)

		self.assertTrue(self.loop.action()) # E
		self.loop.redraw()
		self.assertEqual(self.mock_ui.screen.tostring(), unittest.dedent("""\
		_wielding [a] - None           _
		_wearing  [b] - rags           _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
		self.assertFalse(self.loop.action()) # b
		self.assertEqual(self.game.scene.get_player().inventory, [dagger, rags])
		self.assertIsNone(self.game.scene.get_player().wearing)
