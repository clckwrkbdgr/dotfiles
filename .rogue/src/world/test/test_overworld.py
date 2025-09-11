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
	class Mapping:
		void = Void()
		@staticmethod
		def colored_monster_carrying(pos, *data):
			return PackRat(pos)
		@staticmethod
		def colored_monster(pos, *data):
			return Rat(pos)
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
	MAX_MONSTER_ACTION_LENGTH = 4
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
		self.assertEqual(scene.get_area_rect(), Rect((0, 0), (3*2*2, 3*2*2)))
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
	def should_enter_actor(self):
		scene = MockScene(BUILDERS, RNG(0))
		scene.generate(None)
		rogue = Rogue(None)
		scene.enter_actor(rogue, None)
		self.assertEqual(scene.world.cells.cell((0, 1)).cells.cell((0, 1)).data.monsters[0], rogue)
		self.assertEqual(rogue.pos, Point(0, 1))
	def should_exit_actor(self):
		scene = MockScene(BUILDERS, RNG(0))
		scene.generate(None)
		rogue = Rogue(None)
		scene.enter_actor(rogue, None)
		scene.exit_actor(rogue)
		self.assertEqual(scene.world.cells.cell((0, 1)).cells.cell((0, 1)).data.monsters, [])
	def should_rip_actor(self):
		scene = MockScene(BUILDERS, RNG(0))
		scene.generate(None)
		rogue = Rogue(None)
		dagger = Dagger()
		rogue.grab(dagger)
		scene.enter_actor(rogue, None)
		dropped_items = list(scene.rip(rogue))
		self.assertEqual(scene.world.cells.cell((0, 1)).cells.cell((0, 1)).data.monsters, [])
		self.assertEqual(dropped_items, [dagger])
		self.assertEqual(scene.world.cells.cell((0, 1)).cells.cell((0, 1)).data.items, dropped_items)
	def should_drop_and_take_item(self):
		scene = MockScene(BUILDERS, RNG(0))
		scene.generate(None)
		dagger = Dagger()
		scene.drop_item(ItemAtPos(Point(1, 7), dagger))
		self.assertEqual(scene.world.cells.cell((0, 1)).cells.cell((0, 1)).data.items, [dagger])

		item = scene.take_item(ItemAtPos(Point(1, 7), dagger))
		self.assertEqual(item, dagger)
		self.assertEqual(scene.world.cells.cell((0, 1)).cells.cell((0, 1)).data.items, [])
	def should_recalibrate_scene_by_generating_new_zones(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			False, False, False,
			False, True, False,
			False, False, False,
			])
		scene.recalibrate(Point(5, 5), Size(1, 1))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			False, False, False,
			False, True, False,
			False, False, False,
			])
		scene.recalibrate(Point(4, 5), Size(1, 1))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			False, False, False,
			True, True, False,
			False, False, False,
			])
		scene.recalibrate(Point(4, 4), Size(1, 1))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			True, True, False,
			True, True, False,
			False, False, False,
			])
		scene.recalibrate(Point(7, 4), Size(1, 1))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			True, True, True,
			True, True, True,
			False, False, False,
			])
		scene.recalibrate(Point(7, 7), Size(1, 1))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			True, True, True,
			True, True, True,
			False, True, True,
			])
		scene.recalibrate(Point(4, 7), Size(1, 1))
		self.assertEqual([_ is not None for _ in scene.world.cells.values()], [
			True, True, True,
			True, True, True,
			True, True, True,
			])
	def should_detect_invalid_coords(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		self.assertFalse(scene.valid(Point(-1, -1)))
		self.assertTrue(scene.valid(Point(0, 0)))
		self.assertTrue(scene.valid(Point(4, 4)))
		self.assertFalse(scene.valid(Point(9, 9)))
		self.assertFalse(scene.valid(Point(12, 12)))
	def should_get_cell_info(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		self.assertEqual(repr(scene.get_cell_info(Point(3, 4))), repr((Void(), [], [], [Rat(Point(1, 0))])))
		self.assertEqual(scene.get_cell_info(Point(9, 9)), (None, [], [], []))
	def should_get_global_pos(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		rat = scene.get_cell_info(Point(3, 4))[-1][0]
		self.assertEqual(scene.get_global_pos(rat), Point(3, 4))
	def should_perform_movement(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		rat = scene.get_cell_info(Point(3, 4))[-1][0]
		scene.world.cells.cell((1, 1)).cells.cell((0, 0)).cells.set_cell((0, 0), Floor())
		self.assertTrue(scene.can_move(rat, Point(4, 4)))
		scene.transfer_actor(rat, Point(4, 4))
		self.assertEqual(scene.get_global_pos(rat), Point(3, 4))
	def should_find_items(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		dagger = Dagger()
		scene.drop_item(ItemAtPos(Point(1, 7), dagger))
		self.assertEqual(list(scene.iter_items_at(Point(1, 7))), [dagger])
	def should_find_actors(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		rogue = Rogue(None)
		scene.enter_actor(rogue, None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		rat = scene.get_cell_info(Point(3, 4))[-1][0]
		self.assertEqual(list(scene.iter_actors_at(Point(3, 4))), [rat])
		self.assertEqual(list(scene.iter_actors_at(Point(7, 6))), [])
		self.assertEqual(list(scene.iter_actors_at(Point(7, 6), with_player=True)), [rogue])

		self.assertEqual(sorted(map(repr, scene.iter_actors_in_rect(Rect((0, 0), (6, 6))))), [
			'Rat(rat @[0, 0] 10/10hp)',
			'Rat(rat @[0, 1] 10/10hp)',
			'Rat(rat @[1, 0] 10/10hp)',
			'Rat(rat @[1, 0] 10/10hp)',
			'Rat(rat @[1, 1] 10/10hp)',
			])
		self.assertEqual(list(map(repr, scene.iter_active_monsters())), [
			'Rat(rat @[1, 0] 10/10hp)',
			'Rogue(rogue @[1, 0] 10/10hp)',
			])
	def should_iter_cells(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		scene.recalibrate(Point(7, 4), Size(3, 3))
		scene.recalibrate(Point(4, 7), Size(3, 3))
		self.assertEqual(scene.tostring(Rect((3, 4), (9, 8))), unittest.dedent("""\
		r......rr
		.......rr
		.....rr..
		.....rr..
		....r....
		.........
		.........
		..r......
		""").replace('.', ' '))

class TestVision(unittest.TestCase):
	def should_visit_places_by_monsters(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		rat = scene.get_cell_info(Point(3, 4))[-1][0]
		vision = scene.make_vision(rat)
		vision.visit(rat)
		self.assertTrue(vision.is_visible(Point(2, 4)))
		self.assertFalse(vision.is_visible(Point(6, 8)))
	def should_ignore_monsters_on_first_visit(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		rogue = Rogue(None)
		scene.enter_actor(rogue, None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		vision = scene.make_vision(rogue)
		monsters = list(vision.visit(rogue))
		self.assertEqual(monsters, [])
	def should_visit_places_by_player(self):
		scene = MockScene([MockVoidBuilder], RNG(9))
		scene.generate(None)
		rogue = Rogue(None)
		scene.enter_actor(rogue, None)
		scene.recalibrate(Point(4, 4), Size(3, 3))
		vision = scene.make_vision(rogue)
		vision._first_visit = False
		monsters = list(vision.visit(rogue))
		self.assertEqual(list(map(repr, monsters)), [
			'Rat(rat @[1, 0] 10/10hp)',
			'PackRat(rat @[0, 0] 10/10hp)',
			])
		new_monsters = list(vision.visit(rogue))
		self.assertEqual(new_monsters, [])

		self.assertEqual(list(vision.iter_important()), monsters)
