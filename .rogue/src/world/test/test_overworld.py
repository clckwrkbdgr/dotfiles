from clckwrkbdgr import unittest
from clckwrkbdgr.math.grid import Matrix, Point
from clckwrkbdgr.math.grid import NestedGrid
import clckwrkbdgr.serialize.stream as savefile
from clckwrkbdgr.pcg import RNG
from .. import overworld
from ...engine.items import ItemAtPos
from ...engine.mock import *
from ...engine.test.utils import *

class MockVoidBuilder(overworld.Builder):
	def _make_terrain(self, grid):
		grid.clear('void')
class MockBuilder(object):
	class Mapping:
		dead_tree = plant = Floor()
class MockForest(MockBuilder, overworld.Forest): pass
class MockDesert(MockBuilder, overworld.Desert): pass
class MockThundra(MockBuilder, overworld.Thundra): pass
class MockMarsh(MockBuilder, overworld.Marsh): pass
BUILDERS = [MockForest, MockDesert, MockThundra, MockMarsh]

class MockScene(overworld.Scene):
	SIZE = [(3, 3), (2, 2), (2, 2)]

class TestBuilders(unittest.TestCase):
	def should_generate_basic_grid(self):
		grid = Matrix((16, 16))
		builder = MockVoidBuilder(RNG(1), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring(), '\n'.join(['void'*16]*16) +'\n')
		self.assertEqual(builder.actors, {Point(8, 15):[
			('colored_monster', 'd', 'bold_blue', 0, 1),
			]})
	def should_generate_several_monsters(self):
		grid = Matrix((16, 16))
		builder = MockVoidBuilder(RNG(26), grid)
		builder.generate()
		self.assertEqual(dict(builder.actors), {
			Point(0, 15): [('colored_monster_carrying', 'v', 'white', 1, 0)],
			Point(13, 7): [('colored_monster', 'f', 'magenta', 1, 0)],
			})
	def should_generate_buildings_with_doors_and_dwellers(self):
		grid = Matrix((16, 16))
		builder = MockVoidBuilder(RNG(0), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('void', '_').replace('floor', '.').replace('wall', '#'), unittest.dedent("""\
				________________
				________________
				___########_____
				___#......#_____
				___#......#_____
				___#......#_____
				___#......#_____
				___###.####_____
				________________
				________________
				________________
				________________
				________________
				________________
				________________
				________________
				"""))
		self.assertEqual(builder.actors, {Point(6, 4):[
			('dweller', 'bold_magenta'),
			]})

		builder = MockVoidBuilder(RNG(181), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('void', '_').replace('floor', '.').replace('wall', '#'), unittest.dedent("""\
				________________
				________________
				________________
				________________
				____######______
				____#....#______
				____#....#______
				____#....#______
				____#.....______
				____######______
				________________
				________________
				________________
				________________
				________________
				________________
				"""))

		builder = MockVoidBuilder(RNG(253), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('void', '_').replace('floor', '.').replace('wall', '#'), unittest.dedent("""\
				________________
				________________
				___######_______
				___#....#_______
				___.....#_______
				___#....#_______
				___#....#_______
				___#....#_______
				___#....#_______
				___######_______
				________________
				________________
				________________
				________________
				________________
				________________
				"""))

		builder = MockVoidBuilder(RNG(362), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('void', '_').replace('floor', '.').replace('wall', '#'), unittest.dedent("""\
				________________
				________________
				________________
				________________
				__###.####______
				__#......#______
				__#......#______
				__#......#______
				__#......#______
				__#......#______
				__########______
				________________
				________________
				________________
				________________
				________________
				"""))
	def should_generate_forest(self):
		self.maxDiff = None
		grid = Matrix((16, 16))
		builder = overworld.Forest(RNG(1), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('grass', '.').replace('plant', 'o').replace('bush', '"').replace('tree', 'T'), unittest.dedent("""\
				......T..T......
				.T.........T....
				..."".o.....T...
				..o..T.o.o."T...
				..TT..T........"
				T..T.TT........T
				.........T...T."
				To.TT..........o
				..T...........T.
				.T."..T.......To
				T.T...T........o
				..T.........o..T
				...."."oT.T..".T
				...T..T.....TT..
				....T.......T"..
				.....T.TT..TT...
				"""))
	def should_generate_desert(self):
		self.maxDiff = None
		grid = Matrix((16, 16))
		builder = overworld.Desert(RNG(1), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('sand', '.').replace('plant', 'o').replace('rock', '^'), unittest.dedent("""\
				................
				.o..............
				................
				................
				..^...o.........
				................
				................
				...o............
				................
				................
				..o.............
				..o.............
				........o.o.....
				............o...
				................
				.....o..o.......
				"""))
	def should_generate_thundra(self):
		self.maxDiff = None
		grid = Matrix((16, 16))
		builder = overworld.Thundra(RNG(0), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('snow', '.').replace('ice', '_').replace('frozen_ground', ':'), unittest.dedent("""\
				................
				.........._.....
				................
				..........:.....
				..:..:...._.....
				................
				................
				........_.......
				.......:........
				................
				................
				................
				..........:....:
				.....:..........
				................
				................
				"""))
	def should_generate_marsh(self):
		self.maxDiff = None
		grid = Matrix((16, 16))
		builder = overworld.Marsh(RNG(0), grid)
		builder.generate()
		self.assertEqual(builder.grid.tostring().replace('swamp', '.').replace('bog', '_').replace('grass', '"').replace('dead_tree', 'T'), unittest.dedent('''\
				_.."""."."."".._
				_""""."..."._...
				""._"_...."_".."
				__."""""".__....
				"T_"._....""."_"
				_...""....""".._
				...."T___""."._.
				"_._.._""..."._tree_.
				._._""._...""._T
				__".".._"T""._".
				_.__"T"_._"...__
				_T"_."____."...T
				"""""_".._tree._..._"
				"._.."".."__."__
				."."...T._.__"._
				"_"..""."..."...
				'''))

class TestScene(unittest.TestCase):
	def should_generate_scene_starting_from_a_single_zone(self):
		scene = MockScene(BUILDERS, RNG(0))
		scene.generate(None)
		self.assertEqual(scene._player_pos, NestedGrid.Coord((0, 1), (0, 1), (0, 1)))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [False]*3 + [True] + [False] * 5)
	def should_serialize_and_deserialize_scene(self):
		scene = MockScene(BUILDERS, RNG(0))
		scene.generate(None)
		scene.enter_actor(Rogue(None), None)
		scene.drop_item(ItemAtPos(Point(1, 7), Dagger()))

		writer = savefile.Writer(MockWriterStream(), 1)
		scene.save(writer)
		dump = writer.f.dump[1:]
		self.maxDiff = None
		self.assertEqual(dump, ['3', '3',
					'', '', '',
					'.',
					'2', '2', '2', '2', 'Floor', 'Floor', 'Floor', 'Floor',
					'0', '0', '2', '2', 'Floor', 'Floor', 'Floor', 'Floor',
					'0', '0', '2', '2', 'Floor', 'Floor', 'Floor', 'Floor',
						'1', 'Dagger', '1', '1',
						'1', 'Rogue', '0', '1', '10', '0',
					'0', '0', '2', '2', 'Floor', 'Floor', 'Floor', 'Floor',
					'0',
					'0',
					'', '', '', '', ''
					])
		dump = [str(1)] + list(map(str, dump))

		restored = MockScene(BUILDERS)
		reader = savefile.Reader(iter(dump))
		restored.load(reader)

		self.assertEqual([_ is not None for _ in restored.world.cells.values()], [False]*3 + [True] + [False] * 5)
