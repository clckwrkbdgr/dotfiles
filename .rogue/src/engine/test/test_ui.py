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

class MockMainGame(ui.MainGame):
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
