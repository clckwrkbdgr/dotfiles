from clckwrkbdgr import unittest
from clckwrkbdgr.math.grid import Matrix
from clckwrkbdgr.math import Point, Size, Rect
import clckwrkbdgr.tui
from .. import ui
from .. import Game
from clckwrkbdgr.pcg import RNG
from ..mock import *

class MockUI:
	def __init__(self):
		self.screen = Matrix((30, 7), ' ')
		self._cursor = None
	def print_char(self, x, y, sprite, color):
		self.screen.set_cell((x, y), sprite)
	def print_line(self, y, x, line):
		for i, c in enumerate(line):
			self.screen.set_cell((x + i, y), c)
	def cursor(self, value=None):
		if value is True:
			self._cursor = Point(0, 0)
		elif value is False:
			self._cursor = None
		else:
			return self
	def move(self, x, y):
		self._cursor = Point(x, y)

class MockMainGame(ui.MainGame):
	KEYMAPPING = clckwrkbdgr.tui.Keymapping()
	INDICATORS = [
			ui.Indicator((0, 0), 10, lambda _:'pos: {0}'.format(_.game.scene.get_player().pos)),
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
	def _init(self):
		self.maxDiff = None
		game = NanoDungeon(RNG(0))
		game.generate(None)
		mode = MockMainGame(game)
		mock_ui = MockUI()
		return mode, mock_ui

class TestMainGameDisplay(MainGameTestCase):
	def should_get_visible_sprites(self):
		mode, mock_ui = self._init()
		self.assertEqual(mode.get_sprite(Point(4, 9)), ui.Sprite('#', None))
		self.assertEqual(mode.get_sprite(Point(4, 7)), ui.Sprite('@', None))
		mode.game.scene.get_player().pos = Point(1, 1)
		self.assertEqual(mode.get_sprite(Point(3, 2)), ui.Sprite('&', None))
		self.assertEqual(mode.get_sprite(Point(1, 2)), ui.Sprite('?', None))
	def should_get_remembered_sprites(self):
		mode, mock_ui = self._init()
		self.assertEqual(mode.get_sprite(Point(3, 2)), ui.Sprite('&', None))
		self.assertEqual(mode.get_sprite(Point(1, 2)), None) # ?
		self.assertEqual(mode.get_sprite(Point(0, 0)), ui.Sprite('#', None))
	def should_draw_map(self):
		mode, mock_ui = self._init()

		# To display some void south of the wall:
		mode.game.scene.get_player().pos.y += 1

		mode.draw_map(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_                              _
		_.~...                         _
		_.....                         _
		_.b@..                         _
		_#####                         _
		_                              _
		_                              _
		""").replace('_', ''))
	def should_print_messages(self):
		mode, mock_ui = self._init()
		mode.messages = [
		'Hello, this is the first message and it is long.'
		'Second, also long...',
		'Third.',
		'Last.',
		]

		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"Hello, this is the first...   \n"
			]))
		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			" message and it is long....   \n"
			]))
		mode.print_messages(mock_ui, Point(0, 6), line_width=27)
		self.assertEqual(mock_ui.screen.tostring(), '\n'.join([' '*30]*6+[
			"Second, also long......       \n"
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
		mode, mock_ui = self._init()
		mode.draw_status(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [4, 7]                   _
		_         monsters: 2          _
		_                              _
		_                              _
		_                              _
		_                              _
		_                              _
		""").replace('_', ''))
	def should_show_cursor(self):
		mode, mock_ui = self._init()
		mode.aim = Point(3, 3)
		mode.redraw(mock_ui)
		self.assertEqual(mock_ui._cursor, Point(3, 4))
	def should_draw_everything(self):
		mode, mock_ui = self._init()
		mode.messages = [
		'Hello, this is the first message and it is long.'
		'Second, also long...',
		'Third.',
		'Last.',
		]
		mode.redraw(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_pos: [4, 7]                   _
		_.....    monsters: 2          _
		_.~...                         _
		_..@..                         _
		_.b...                         _
		_#####                         _
		_Hello, this is the first...   _
		""").replace('_', ''))

class TestMainGameCustomizations(MainGameTestCase):
	def should_disable_keymapping_when_player_does_not_control(self):
		mode, mock_ui = self._init()
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
		mode, mock_ui = self._init()
		self.assertTrue(mode.pre_action())
		mode.game.scene.monsters.remove(mode.game.scene.get_player())
		self.assertFalse(mode.pre_action())
	def should_perform_post_actions(self):
		mode, mock_ui = self._init()
		self.assertTrue(mode.action(False))
		self.assertFalse(mode.action(True))

		mode.messages.append('mock message')
		self.assertTrue(mode.action(clckwrkbdgr.tui.Key(' ')))
		mode.messages = []

		mode.game.scene.monsters.remove(mode.game.scene.get_player())
		self.assertFalse(mode.action(clckwrkbdgr.tui.Key(' ')))
