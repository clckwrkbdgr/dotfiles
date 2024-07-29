import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
from .. import builders
from ...math import Point, Size
from .._base import RNG
from .. import _base as pcg

STR_TERRAIN = {
		None : ' ',
		'wall' : '#',
		'floor' : ".",
		'water' : "~",
		'corner' : "+",
		'wall_h' : "-",
		'wall_v' : "|",
		'door' : "+",
		'passage' : "#",
		}
def str_terrain(name):
	return STR_TERRAIN[name]

class MockBuilder(builders.Builder):
	def _build(self):
		for x in range(self.size.width):
			self.strata.set_cell(x, 0, 'wall')
			self.strata.set_cell(x, self.size.height - 1, 'wall')
		for y in range(self.size.height):
			self.strata.set_cell(0, y, 'wall')
			self.strata.set_cell(self.size.width - 1, y, 'wall')
		for x in range(1, self.size.width - 1):
			for y in range(1, self.size.height - 1):
				self.strata.set_cell(x, y, 'floor')
		floor_only = lambda pos: self.strata.cell(pos.x, pos.y) == 'floor'
		obstacle_pos = pcg.pos(self.rng, self.size, floor_only)
		self.strata.set_cell(obstacle_pos.x, obstacle_pos.y, 'wall')
		self.start_pos = pcg.pos(self.rng, self.size, floor_only)
		self.exit_pos = pcg.pos(self.rng, self.size, floor_only)

class TestBuilder(unittest.TestCase):
	def should_generate_dungeon(self):
		rng = RNG(0)
		builder = MockBuilder(rng, Size(20, 20))
		builder.build()
		self.assertEqual(builder.start_pos, Point(9, 12))
		self.assertEqual(builder.exit_pos, Point(7, 16))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				####################
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				#.....#............#
				#..................#
				#..................#
				#..................#
				#..................#
				#..................#
				####################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)

class TestRogueDungeon(unittest.TestCase):
	def should_generate_rogue_dungeon(self):
		rng = RNG(1)
		builder = builders.RogueDungeon(rng, Size(80, 25))
		builder.build()
		self.assertEqual(builder.start_pos, Point(37, 13))
		self.assertEqual(builder.exit_pos, Point(18, 11))
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
		self.assertEqual(builder.strata.tostring(str_terrain), expected)
	def should_generate_small_rogue_dungeon(self):
		rng = RNG(0)
		builder = builders.RogueDungeon(rng, Size(11, 11))
		builder.build()
		self.assertEqual(builder.start_pos, Point(9, 4))
		self.assertEqual(builder.exit_pos, Point(9, 8))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				+--+--+---+
				|..|+.|...|
				|..+..|...|
				+--+--+-+-+
				|..+..|.+.|
				|..|..|...|
				+--++-++--+
				|..++.+.+.|
				|..|..|+..|
				|..|..|...|
				+--+--+---+
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)

class TestBSPDungeon(unittest.TestCase):
	def should_generate_bsp_dungeon(self):
		rng = RNG(0)
		builder = builders.BSPDungeon(rng, Size(80, 25))
		builder.build()
		self.assertEqual(builder.start_pos, Point(31, 20))
		self.assertEqual(builder.exit_pos, Point(29, 2))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				################################################################################
				#................#..........#.......#................#.......#............#....#
				#................#..........#.......#................#.......#............#....#
				#................#..........#.......#........................#.................#
				#...........................#........................#.......#............#....#
				#................#..................#................#.......#............#....#
				#................#..........#.......#................#....................#....#
				#................#..........#.......#................#.......#............#....#
				#................#..........#.......#................#.......#............#....#
				####################################################.###########################
				#..............#.....#.............#.....#.......#............#.......#......#.#
				#..............#.....#.............#.....#.......#............#.......#......#.#
				#..............#.....#.............#.....#....................#..............#.#
				#..............#.....#.............#.....#.......#....................#......#.#
				#..............#.....#.............#.............#............#.......#......#.#
				#..............#.........................#.......#............#.......#......#.#
				#....................#.............#.....#.......#............#.......#......#.#
				#..............#.....#.............#.....#.......#............#.......#......#.#
				##########################################.###################################.#
				#...........#.....#........#...............#...........#......#........#.....#.#
				#...........#.....#........#...............#...........#......#........#.......#
				#...........#..............#...............#...........#.....................#.#
				#.................#...........................................#........#.....#.#
				#...........#.....#........#...............#...........#......#........#.....#.#
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)

class TestBSPCityBuilder(unittest.TestCase):
	def should_generate_bsp_dungeon(self):
		rng = RNG(0)
		builder = builders.CityBuilder(rng, Size(80, 25))
		builder.build()
		self.assertEqual(builder.start_pos, Point(11, 1))
		self.assertEqual(builder.exit_pos, Point(58, 22))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				################################################################################
				#..............................................................................#
				#..............................................................................#
				#..............................................................................#
				#...#########################...############################################...#
				#...#########################...############################################...#
				#...#########################...############################################...#
				#...#########################...############################################...#
				#...#########################...############################################...#
				#...#########################...############################################...#
				#...#########################...############################################...#
				#..............................................................................#
				#..............................................................................#
				#..............................................................................#
				#...###############################...########...#####...############...####...#
				#...###############################...########...#####...############...####...#
				#...###############################...########...#####...############...####...#
				#...###############################...########...#####...############...####...#
				#...###############################...########...#####...############...####...#
				#...###############################...########...#####...############...####...#
				#...###############################...########...#####...############...####...#
				#..............................................................................#
				#..............................................................................#
				#..............................................................................#
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)

class TestCaveDungeon(unittest.TestCase):
	def should_generate_cave_dungeon(self):
		rng = RNG(0)
		builder = builders.CaveBuilder(rng, Size(80, 25))
		builder.build()
		self.assertEqual(builder.start_pos, Point(51, 2))
		self.assertEqual(builder.exit_pos, Point(52, 3))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				################################################################################
				########.#######......####..........#.........###########...#.#...............##
				#...###....####................................##...###........................#
				#....####...#..........##......................##..............................#
				#............................#.....#...........................................#
				#..............#............###...###........................##....####........#
				#...........####............##....####...####.......#####.........######......##
				#...........####............##....###...#######....#######........#######.....##
				#...........###...........##.......##...########...................######....###
				##.....................###..............#######...............#....######....###
				####..................####..............####.........................###......##
				####...................#................##....................................##
				#####.............#................##.......................................#.##
				####..............................####......................................#.##
				##......###.........#.#............###.......................##................#
				#.......####........#####.#.##.....####....................####................#
				#.......####........############....###....................###................##
				#.......#####........##########......###..............#.......................##
				#......#####.........#######.........##...##.................................###
				#....#######..........#####..........###..##..................................##
				#...######.............##.................##..................................##
				#....###...............#......##....###...###..................................#
				#............................####.........####.................................#
				##............#####...##....############.#######..###......###................##
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)

class TestMazeDungeon(unittest.TestCase):
	def should_generate_maze(self):
		rng = RNG(0)
		builder = builders.MazeBuilder(rng, Size(80, 25))
		builder.build()
		self.assertEqual(builder.start_pos, Point(7, 4))
		self.assertEqual(builder.exit_pos, Point(31, 17))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				################################################################################
				#.#.....#.#.....#.......#...#...#...#...#.....#...#...........#.....#...#...#.##
				#.#.#.#.#.#.###.#.#####.#.#.#.#.#.#.###.#.###.#.###.#########.#.###.###.#.#.#.##
				#...#.#.#.....#.....#.#.#.#.#.#.#.#.#...#...#.......#.........#.#...#...#.#.#.##
				#.#.#.#.###########.#.#.#.#.###.#.#.#.###.#.#######.#.###########.###.###.#.#.##
				#.#.#.#.......#.....#...#.#...#...#.#.....#.#.....#.#...#...#.............#.#.##
				###.#.#######.#.#####.###.###.#.###.#######.#.#####.###.#.###.###.#########.#.##
				#...#.#.#...#.#.....#.#.#.#.#...#.#.....#.#.#.....#.#...#...#.#...#...#.....#.##
				#.#.#.#.#.#.#.#####.#.#.#.#.#.###.#.###.#.#.#####.#.#.#####.#.#####.#.#######.##
				#.#.#.#.#.#.#.......#.#.#.#...#.......#.#.#.#.....#.#.#...#.#.......#.#.......##
				#.#.#.#.#.#.#.#######.#.#.#########.###.#.#.#.#####.#.###.#.#########.#.#####.##
				#.#.#.#.#.#...#.....#.....#.#.....#...#...#.#.....#.#.#...#...#.......#.....#.##
				###.#.#.#.#####.###.#######.#.###.#.#.#####.#####.#.#.#.#.#.#.#.#########.#.####
				#...#...#.#...#.#.......#...#...#.#.#.....#.......#.#.#.#.#.#...#.........#...##
				#.#######.#.###.#.#####.#.#####.###.#####.#.###.###.#.#.#.#.#################.##
				#.#.......#.....#.....#.#.....#.....#...#.#.#.#...#.#.#.#.#.........#...#.#...##
				###.#########.#######.#.###.#.#########.#.#.#.###.#.#.#.###.#######.#.#.#.#.####
				#.#.#.........#.#...#.#...#.#.....#.....#.#.#.....#.#.....#...#...#.#.#.#...#.##
				#.#.###.#######.#.#.#####.#.#####.###.#.#.#.#.#####.#####.#.#.#.###.#.#.#.#.#.##
				#.....#.......#.#.#.....#.#.....#.....#.#.#.#.#...#.....#.#.#.#...#.#.#...#.#.##
				#.###.#######.#.#.###.#.#.#.#############.#.###.#.#####.#.#.#.#.#.#.#.#.###.#.##
				#...#.......#...#.#.#.#.#.#...#...........#...#.#...#...#.#.#.#.#.#...#...#.#.##
				###.###.#.#.#####.#.#.###.###.#.#.#########.#.###.#.#.###.###.#.#.#########.#.##
				#...#...#.#.........#.......#...#...........#.....#.#...#.....#.#.............##
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)
	def should_generate_maze_without_hanging(self):
		rng = RNG(2087627623)
		builder = builders.MazeBuilder(rng, Size(80, 23))
		builder.build()
		self.assertEqual(builder.start_pos, Point(29, 7))
		self.assertEqual(builder.exit_pos, Point(43, 1))
		self.maxDiff = None
		expected = textwrap.dedent("""\
				################################################################################
				#...................#...#.........#.#.....#...#...........#.#...#.........#...##
				#.#################.#.#.#.#######.#.#.###.###.#.#.#######.#.#.#.###.###.###.#.##
				#...#.....#...#.....#.#.#.#...#.#.#.#.#.#.....#.#.#.....#.....#...#...#.....#.##
				###.#.###.#.###.#####.###.###.#.#.#.#.#.#######.#.#.#######.#####.###.#######.##
				#...#.#...#.....#...#.....#...#...#...#.#.......#.#.....#...#...#.....#...#...##
				#.###.#.#########.#.#####.#.###.#.###.#.#.#############.#.#.#.#########.#.#.####
				#...#.#.......#...#.......#.....#...#.#.#...............#.#.#...........#.#.#.##
				###.#.#####.#.#.#####################.#.###.#######.#####.#.#########.#####.#.##
				#...#.#.....#.#.......#.....#...........#...#.......#.#...#.#.......#.......#.##
				#.###.#.#.###########.#.#.#.#.###########.###.#.#####.#.#####.#####.#########.##
				#.....#.#.....#...#.#.#.#.#.#.............#...#.......#.......#.......#.......##
				#######.#####.#.#.#.#.###.#.#######.#######################.#########.#.###.####
				#.....#.#.#.....#.....#...#.......#...#.....#...........#...#...........#.#.#.##
				#.#####.#.#.###########.###########.#.#.###.#.#####.###.#####.###.#.###.#.#.#.##
				#...#...#...#.....#.....#.#.........#.#.#.#.......#...#.#.....#...#.#.#.#...#.##
				###.#.#.#.#######.#.#####.#.###.#######.#.#############.#.#########.#.#.#####.##
				#...#.#.#...............#...#...#.......#...........#...#.........#.#.#.#.....##
				#.###.#####.###########.#####.###.#######.#########.#.#########.#.#.#.#.#.###.##
				#...#.....#.#...#...#.#.#.....#...#.....#.#.#.....#.#.....#.....#.#.#.#.#...#.##
				#.#####.#.#.#.#.#.#.#.#.#.#########.#####.#.#.###.#.#####.#.#####.#.#.#.###.#.##
				#.......#.#...#...#...#.....................#...#.........#.....#.#...#.....#.##
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)

class TestSewers(unittest.TestCase):
	def should_generate_sewers_maze(self):
		rng = RNG(0)
		builder = builders.Sewers(rng, Size(80, 25))
		builder.build()
		self.maxDiff = None
		self.assertEqual(builder.start_pos, Point(10, 13))
		self.assertEqual(builder.exit_pos, Point(17, 8))
		expected = textwrap.dedent("""\
				################################################################################
				#....................####....####............................................###
				#.~~~~~~~~~~~~~~~~~~.####.~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.###
				#.........~~......~~.####.~~.####.~~......................................~~.###
				#########.~~.####.~~.####.~~.####.~~.####################################.~~.###
				#########.~~.####.~~.####.~~.####.~~.####################################.~~.###
				#########.~~.####.~~.####.~~.####.~~.####################################.~~.###
				#.........~~.####.~~.####.~~......~~.####............................####.~~.###
				#.~~~~~~~~~~.####.~~.####.~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~.####.~~.###
				#.~~.........####.~~.####.........~~.####.~~......................~~.####.~~.###
				#.~~.############.~~.############.~~.####.~~.####################.~~.####.~~.###
				#.~~.############.~~.############.~~.####.~~.####################.~~.####.~~.###
				#.~~.############.~~.############.~~.####.~~.####################.~~.####.~~.###
				#.~~.####.........~~..............~~.####.~~.####............####.~~.####.~~.###
				#.~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~.####.~~.####.~~~~~~~~~~.####.~~.####.~~.###
				#....####.~~......~~.................####.~~.####.~~.........####.~~.####.~~.###
				#########.~~.####.~~.####################.~~.####.~~.############.~~.####.~~.###
				#########.~~.####.~~.####################.~~.####.~~.############.~~.####.~~.###
				#########.~~.####.~~.####################.~~.####.~~.############.~~.####.~~.###
				#.........~~.####.~~......................~~.####.~~..............~~.####.~~.###
				#.~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~.####.~~.###
				#............####............................####....................####....###
				################################################################################
				################################################################################
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)
	def should_not_skip_fringe_rows_in_odd_height_mazes(self):
		rng = RNG(856411207)
		builder = builders.Sewers(rng, Size(80, 23))
		builder.build()
		self.maxDiff = None
		self.assertEqual(builder.start_pos, Point(68, 18))
		self.assertEqual(builder.exit_pos, Point(57, 11))
		expected = textwrap.dedent("""\
				################################################################################
				#............####....................................####....................###
				#.~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~.###
				#.~~......~~.####.~~..............................~~.####.~~.................###
				#.~~.####.~~.####.~~.############################.~~.####.~~.###################
				#.~~.####.~~.####.~~.############################.~~.####.~~.###################
				#.~~.####.~~.####.~~.############################.~~.####.~~.###################
				#.~~.####.~~.####.~~.####....................####.~~......~~.................###
				#.~~.####.~~.####.~~.####.~~~~~~~~~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~.###
				#.~~.####....####.~~.####.~~..............~~.####.........~~..............~~.###
				#.~~.############.~~.####.~~.############.~~.############.~~.############.~~.###
				#.~~.############.~~.####.~~.############.~~.############.~~.############.~~.###
				#.~~.############.~~.####.~~.############.~~.############.~~.############.~~.###
				#.~~.####.........~~.####.~~.........####.~~.####.........~~.####.........~~.###
				#.~~.####.~~~~~~~~~~.####.~~~~~~~~~~.####.~~.####.~~~~~~~~~~.####.~~~~~~~~~~.###
				#.~~.####.~~.........####.........~~.####.~~.####............####.~~......~~.###
				#.~~.####.~~.####################.~~.####.~~.####################.~~.####.~~.###
				#.~~.####.~~.####################.~~.####.~~.####################.~~.####.~~.###
				#.~~.####.~~.####################.~~.####.~~.####################.~~.####.~~.###
				#.~~......~~.####.................~~.####.~~......................~~.####.~~.###
				#.~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~.####.~~~~~~~~~~~~~~~~~~~~~~~~~~.####.~~.###
				#............####....................####............................####....###
				################################################################################
				""")
		self.assertEqual(builder.strata.tostring(str_terrain), expected)
