from clckwrkbdgr import unittest
import textwrap
from clckwrkbdgr.math import Size, Point, Matrix
from .._base import RNG
from .. import rogue

class TestRogueDungeon(unittest.TestCase):
	def _to_string(self, builder):
		grid = Matrix(builder.size, ' ')
		for room in builder.iter_rooms():
			grid.set_cell((room.topleft.x, room.topleft.y), '+')
			grid.set_cell((room.topleft.x, room.topleft.y+room.size.height), '+')
			grid.set_cell((room.topleft.x+room.size.width, room.topleft.y), '+')
			grid.set_cell((room.topleft.x+room.size.width, room.topleft.y+room.size.height), '+')
			for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
				grid.set_cell((x, room.topleft.y), '-')
				grid.set_cell((x, room.topleft.y+room.size.height), '-')
			for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
				grid.set_cell((room.topleft.x, y), '|')
				grid.set_cell((room.topleft.x+room.size.width, y), '|')
			for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
				for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
					grid.set_cell((x, y), '.')

		for tunnel in builder.iter_tunnels():
			for cell in tunnel.iter_points():
				grid.set_cell(cell, '#')
			grid.set_cell(tunnel.start, '+')
			grid.set_cell(tunnel.stop, '+')
		return grid

	def should_generate_rogue_dungeon(self):
		rng = RNG(1)
		builder = rogue.Dungeon(rng, Size(80, 25), Size(3, 3), Size(4, 4))
		builder.generate_rooms()
		builder.generate_maze()
		builder.generate_tunnels()
		grid = self._to_string(builder)

		self.maxDiff = None
		expected = textwrap.dedent("""\
				_                          +----------------------+                            _
				_  +-------------+         |......................| +-------------+            _
				_  |.............+#######  |......................|#+.............|            _
				_  |.............|      ###+......................+#|.............|            _
				_  |.............|         +---------------------++ |.............|            _
				_  +------+------+                               #  +-------------+            _
				_         ##############      ####################                             _
				_                      #      #                                                _
				_                      #      #                       +--------------------+   _
				_              +-------++    ++------------------+    |....................|   _
				_              |........|    |...................+####+....................|   _
				_              |........|    |...................|    |....................|   _
				_              |........|    |...................|    +-----+--------------+   _
				_              |........|    |...................|          ######             _
				_              +---+----+    ++------------------+               #             _
				_              #####          ####################               #             _
				_      +-------+--+               +--------------++   +----------+----------+  _
				_      |..........|               |...............| ##+.....................|  _
				_      |..........|               |...............| # |.....................|  _
				_      |..........|               |...............+## |.....................|  _
				_      |..........|               |...............|   |.....................|  _
				_      |..........|               |...............|   |.....................|  _
				_      +----------+               +---------------+   +---------------------+  _
				_                                                                              _
				_                                                                              _
				""").replace('_', ' ')
		self.assertEqual(grid.tostring(), expected)
