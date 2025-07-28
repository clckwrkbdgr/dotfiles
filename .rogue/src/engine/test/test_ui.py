from clckwrkbdgr import unittest
from clckwrkbdgr.math.grid import Matrix
from clckwrkbdgr.math import Point, Size, Rect
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
	def get_sprite(self, world_pos, cell_info):
		return ui.Sprite(self.game.scene.str_cell(world_pos) or ' ', None)

class TestMainGame(unittest.TestCase):
	def should_draw_map(self):
		game = NanoDungeon(RNG(0))
		game.generate()
		mode = MockMainGame(game)
		mock_ui = MockUI()
		mode.draw_map(mock_ui)
		self.maxDiff = None
		self.assertEqual(mock_ui.screen.tostring(), unittest.dedent("""\
		_                              _
		_.....                         _
		_.~...                         _
		_..@..                         _
		_.b...                         _
		_#####                         _
		_                              _
		""").replace('_', ''))
	def should_print_messages(self):
		self.maxDiff = None
		game = NanoDungeon(RNG(0))
		game.generate()
		mode = MockMainGame(game)
		mode.messages = [
		'Hello, this is the first message and it is long.'
		'Second, also long...',
		'Third.',
		'Last.',
		]
		mock_ui = MockUI()

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
		game = NanoDungeon(RNG(0))
		game.generate()
		mode = MockMainGame(game)
		mock_ui = MockUI()
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
		game = NanoDungeon(RNG(0))
		game.generate()
		mode = MockMainGame(game)
		mock_ui = MockUI()
		mode.aim = Point(3, 3)
		mode.redraw(mock_ui)
		self.assertEqual(mock_ui._cursor, Point(3, 4))
	def should_draw_everything(self):
		game = NanoDungeon(RNG(0))
		game.generate()
		mode = MockMainGame(game)
		mock_ui = MockUI()
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
