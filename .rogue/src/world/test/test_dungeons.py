from clckwrkbdgr import unittest
import textwrap
from clckwrkbdgr.math import Point, Size, Rect, Direction
from clckwrkbdgr.pcg import RNG
from ..dungeonbuilders import CustomMap
from ...engine import items, terrain
from ... import engine
from .. import dungeons as game
from ...engine.mock import *

class NonDiagonalTunnel(terrain.Terrain):
	_name = ','
	_sprite = Sprite(",", None)
	_passable = True
	_remembered=Sprite(',', None)
	_allow_diagonal=False
	_dark=True
class NonDiagonalOblivionTunnel(terrain.Terrain):
	_name = ','
	_sprite = Sprite(",", None)
	_passable = True
	_allow_diagonal=False
	_dark=True
class DarkFloor(terrain.Terrain):
	_name = '+'
	_sprite = Sprite("+", None)
	_passable = True
	_remembered=Sprite('+', None)
	_allow_diagonal=False
	_dark=True

class MockGame(engine.Game):
	def make_player(self):
		player = Rogue(None)
		return player
	def make_scene(self, scene_id):
		_DATA = {
			'fighting around': _MockBuilder,
			}
		return game.Scene(self.rng, [_DATA[scene_id]])

class MockMapping:
	_ = {
		' ' : Void(),
		'#' : Wall(),
		'.' : Floor(),
		# Rogue dungeon:
		'*' : NonDiagonalTunnel(),
		'%' : NonDiagonalOblivionTunnel(),
		'+' : DarkFloor(),
		}
	@staticmethod
	def start(): return 'start'
	@staticmethod
	def exit(): return StairsDown(None, 'enter')
	@staticmethod
	def pack_rat(pos,*data):
		return PackRat(*(data + (pos,)))
	@staticmethod
	def potion(*data):
		return Potion(*data)

class _MockBuilder(CustomMap):
	Mapping = MockMapping
	MAP_DATA = """\
		####################
		#........#>##......#
		#........#..#......#
		#....##..##.#......#
		#....#.............#
		#....#.............#
		#........@.........#
		#..................#
		#..................#
		####################
		"""
	def generate_actors(self):
		self.rng.choice([1]) # FIXME mock action just to shift RNG
		yield (Point(10, 6), 'pack_rat',)
		yield (Point(9, 4), 'pack_rat',)
	def generate_items(self):
		yield (Point(10, 6), 'potion')
		yield (Point(11, 6), 'potion')

class _MockMiniRogue(CustomMap):
	Mapping = MockMapping
	MAP_DATA = """\
		  #### % 
		* #@.# % 
		**+..+%% 
		  #.>#   
		  ####   
		"""

class AbstractTestDungeon(unittest.TestCase):
	def _formatMessage(self, msg, standardMsg): # pragma: no cover
		if hasattr(self, 'dungeon'):
			msg = (msg or '') + '\n' + self.dungeon.scene.tostring(self.dungeon.scene.get_area_rect())
		return super(AbstractTestDungeon, self)._formatMessage(msg, standardMsg)

class TestMonsters(AbstractTestDungeon):
	def should_treat_all_monsters_as_active(self):
		dungeon = self.dungeon = MockGame(0)
		dungeon.generate('fighting around')
		self.assertEqual(list(self.dungeon.scene.iter_active_monsters()), self.dungeon.scene.monsters)
	def should_iter_monsters_in_rect(self):
		dungeon = self.dungeon = MockGame(0)
		dungeon.generate('fighting around')
		self.assertEqual(list(self.dungeon.scene.iter_actors_in_rect(
			Rect((8, 5), Size(3, 3))
			)), self.dungeon.scene.monsters[:2])
	def should_give_monsters_vision(self):
		dungeon = self.dungeon = MockGame(0)
		dungeon.generate('fighting around')
		monster = self.dungeon.scene.monsters[1]
		vision = dungeon.scene.make_vision(monster)
		vision.visit(monster)
		self.assertFalse(vision.is_visible(Point(30, 30)))
		self.assertTrue(vision.is_visible(Point(10, 6)))
		self.assertFalse(vision.is_visible(Point(1, 3)))

class TestItems(AbstractTestDungeon):
	def should_grab_items(self):
		scene = game.Scene(RNG(0), [_MockBuilder])
		scene.generate('potions lying around 2')
		item = scene.take_item(next(scene.iter_items_at((10, 6))))
		self.assertEqual(item.name, 'potion')
		self.assertIsNone(next(scene.iter_items_at((10, 6)), None))
	def should_drop_items(self):
		scene = game.Scene(RNG(0), [_MockBuilder])
		scene.generate('lonely')
		scene.drop_item(items.ItemAtPos((10, 6), Potion()))
		self.assertEqual(next(scene.iter_items_at((10, 6))).name, 'potion')
	def should_drop_loot_from_monsters(self):
		scene = game.Scene(RNG(0), [_MockBuilder])
		scene.generate('fighting around')
		pos = scene.monsters[1].pos
		potion = Potion()
		gold = scene.monsters[1].inventory[0]
		scene.monsters[1].grab(potion)
		self.assertEqual(list(scene.rip(scene.monsters[1])), [potion, gold])
		self.assertEqual(len(scene.monsters), 1)
		self.assertEqual(next(scene.iter_items_at(pos)).name, 'potion')

class TestVisibility(AbstractTestDungeon):
	def should_iter_scene_cells(self):
		scene = game.Scene(RNG(0), [_MockBuilder])
		scene.generate('lonely')
		self.assertEqual(scene.tostring(scene.get_area_rect()), textwrap.dedent("""\
		####################
		#........#>##......#
		#........#..#......#
		#....##..##.#......#
		#....#...r.........#
		#....#.............#
		#.........r!.......#
		#..................#
		#..................#
		####################
		"""))
	def should_list_important_events(self):
		scene = game.Scene(RNG(0), [_MockBuilder])
		scene.generate('fighting around')
		scene.enter_actor(Rogue(Point(9, 6)), None)
		vision = scene.make_vision(scene.get_player())
		list(vision.visit(scene.get_player()))
		self.assertEqual(list(vision.iter_important()), [
			next(scene.iter_actors_at((10, 6))),
			next(scene.iter_actors_at((9, 4))),
			])
	def should_get_visible_surroundings(self):
		scene = game.Scene(RNG(0), [_MockBuilder])
		scene.generate('lonely')
		scene.enter_actor(Rogue(Point(9, 6)), None)
		vision = scene.make_vision(scene.get_player())
		self.assertEqual(scene.get_area_rect(), Rect(Point(0, 0), Size(20, 10)))
		list(vision.visit(scene.get_player()))
		self.assertTrue(vision.is_visible(Point(9, 6)))
		self.assertFalse(vision.is_visible(Point(0, 0)))
		self.assertTrue(vision.is_explored(Point(9, 6)))
		self.assertFalse(vision.is_explored(Point(0, 0)))
		self.assertEqual(vision.visited.tostring(lambda c:'*' if c else '.'), textwrap.dedent("""\
		....*****........*..
		.....****...*..***..
		......***..**.*****.
		.....**************.
		.....**************.
		*******************.
		********************
		*******************.
		*******************.
		.*****************..
		"""))
		scene.get_player().pos = Point(11, 2)
		list(vision.visit(scene.get_player()))
		self.assertEqual(vision.visited.tostring(lambda c:'*' if c else '.'), textwrap.dedent("""\
		....*******......*..
		.....********..***..
		......*******.*****.
		.....**************.
		.....**************.
		*******************.
		********************
		*******************.
		*******************.
		.*****************..
		"""))
	def should_reduce_visibility_at_dark_tiles(self):
		scene = game.Scene(RNG(0), [_MockMiniRogue])
		scene.generate('mini dark rogue')
		scene.enter_actor(Rogue(Point(3, 1)), None)
		vision = scene.make_vision(scene.get_player())
		list(vision.visit(scene.get_player()))
		self.assertEqual(vision.visited.tostring(lambda c:'*' if c else '.'), textwrap.dedent("""\
		..****...
		..****...
		..****...
		..****...
		..****...
		"""))
		scene.get_player().pos = Point(6, 2)
		list(vision.visit(scene.get_player()))
		self.assertEqual(vision.visited.tostring(lambda c:'*' if c else '.'), textwrap.dedent("""\
		..****...
		..******.
		..******.
		..******.
		..****...
		"""))
		scene.get_player().pos = Point(7, 0)
		list(vision.visit(scene.get_player()))
		self.assertEqual(vision.visited.tostring(lambda c:'*' if c else '.'), textwrap.dedent("""\
		..*******
		..*******
		..******.
		..******.
		..****...
		"""))

class TestMovement(AbstractTestDungeon):
	def should_detect_invalid_coords(self):
		scene = game.Scene(RNG(0), [_MockMiniRogue])
		scene.generate('mini rogue lonely')
		self.assertTrue(scene.valid(Point(0, 0)))
		self.assertFalse(scene.valid(Point(0, -1)))
	def should_not_allow_move_player_diagonally_both_from_and_to_good_cell(self):
		scene = game.Scene(RNG(0), [_MockMiniRogue])
		scene.generate('mini rogue lonely')
		scene.enter_actor(Rogue(Point(3, 1)), None)

		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.RIGHT))
		scene.get_player().pos = Point(4, 1)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.DOWN_RIGHT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.DOWN))
		scene.get_player().pos = Point(4, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.RIGHT))
		scene.get_player().pos = Point(5, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.RIGHT))
		scene.get_player().pos = Point(6, 2)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.UP_RIGHT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.RIGHT))
		scene.get_player().pos = Point(7, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.UP))
		scene.get_player().pos = Point(7, 1)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.DOWN_LEFT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.DOWN))
		scene.get_player().pos = Point(7, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.LEFT))
		scene.get_player().pos = Point(6, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.LEFT))
		scene.get_player().pos = Point(5, 2)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.DOWN_LEFT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.LEFT))
		scene.get_player().pos = Point(4, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + Direction.DOWN))
		scene.get_player().pos = Point(4, 3)
	def should_leave_scene(self):
		scene = game.Scene(RNG(0), [_MockMiniRogue])
		scene.generate('mini rogue lonely/1')
		self.assertTrue(scene.one_time())
		player = Rogue(Point(3, 1))
		scene.enter_actor(player, None)
		self.assertEqual(scene.exit_actor(player), player)
