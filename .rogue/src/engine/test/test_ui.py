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
	def print_char(self, x, y, sprite, color):
		self.screen.set_cell((x, y), sprite)
	def print_line(self, y, x, line):
		for i, c in enumerate(line):
			self.screen.set_cell((x + i, y), c)

class MockMainGame(ui.MainGame):
	INDICATORS = [
			ui.Indicator((0, 0), 10, lambda _:'pos: {0}'.format(_.game.scene.get_player().pos)),
			ui.Indicator((9, 1), 10, lambda _:'monsters: {0}'.format(len(_.game.scene.monsters))),
			]
	def get_map_shift(self):
		return Point(0, 1)
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
