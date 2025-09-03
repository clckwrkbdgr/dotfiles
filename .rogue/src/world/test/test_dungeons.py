import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point, Size, Rect
from clckwrkbdgr.pcg import RNG
from ..dungeonbuilders import builders
from ...engine import items
from ... import engine
from .. import dungeons as game
import clckwrkbdgr.serialize.stream as savefile
from . import mock_dungeon
from .mock_dungeon import MockGame

class AbstractTestDungeon(unittest.TestCase):
	def _formatMessage(self, msg, standardMsg): # pragma: no cover
		if hasattr(self, 'dungeon'):
			msg = (msg or '') + '\n' + self.dungeon.scene.tostring(self.dungeon.scene.get_area_rect())
		return super(AbstractTestDungeon, self)._formatMessage(msg, standardMsg)

class TestMonsters(AbstractTestDungeon):
	def should_treat_all_monsters_as_active(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		self.assertEqual(list(self.dungeon.scene.iter_active_monsters()), self.dungeon.scene.monsters)
	def should_iter_monsters_in_rect(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		self.assertEqual(list(self.dungeon.scene.iter_actors_in_rect(
			Rect((8, 5), Size(3, 3))
			)), self.dungeon.scene.monsters[:2])
	def should_give_monsters_vision(self):
		dungeon = self.dungeon = mock_dungeon.build('fighting around')
		monster = self.dungeon.scene.monsters[1]
		vision = dungeon.scene.make_vision(monster)
		vision.visit(monster)
		self.assertFalse(vision.is_visible(Point(30, 30)))
		self.assertTrue(vision.is_visible(Point(10, 6)))
		self.assertFalse(vision.is_visible(Point(1, 3)))

class TestItems(AbstractTestDungeon):
	def should_grab_items(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockBuilder_PotionsLyingAround])
		scene.generate('potions lying around 2')
		item = scene.take_item(next(scene.iter_items_at((10, 6))))
		self.assertEqual(item.name, 'potion')
		self.assertIsNone(next(scene.iter_items_at((10, 6)), None))
	def should_drop_items(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockBuilderUnSettler])
		scene.generate('lonely')
		scene.drop_item(items.ItemAtPos((10, 6), mock_dungeon.Potion()))
		self.assertEqual(next(scene.iter_items_at((10, 6))).name, 'potion')
	def should_drop_loot_from_monsters(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockBuilder_FightingGround])
		scene.generate('fighting around')
		pos = scene.monsters[1].pos
		potion = mock_dungeon.Potion()
		scene.monsters[1].grab(potion)
		self.assertEqual(list(scene.rip(scene.monsters[1])), [potion])
		self.assertEqual(len(scene.monsters), 1)
		self.assertEqual(next(scene.iter_items_at(pos)).name, 'potion')

class TestVisibility(AbstractTestDungeon):
	def should_iter_scene_cells(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockBuilderUnSettler])
		scene.generate('lonely')
		self.assertEqual(scene.tostring(scene.get_area_rect()), textwrap.dedent("""\
		####################
		#........#>##......#
		#........#..#......#
		#....##..##.#......#
		#....#.............#
		#....#.............#
		#.........!........#
		#..................#
		#..................#
		####################
		"""))
	def should_list_important_events(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockBuilder_FightingGround])
		scene.generate('fighting around')
		scene.enter_actor(mock_dungeon.Player(Point(9, 6)), None)
		vision = scene.make_vision(scene.get_player())
		list(vision.visit(scene.get_player()))
		self.assertEqual(list(vision.iter_important()), [
			next(scene.iter_actors_at((10, 6))),
			next(scene.iter_actors_at((9, 4))),
			])
	def should_get_visible_surroundings(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockBuilderUnSettler])
		scene.generate('lonely')
		scene.enter_actor(mock_dungeon.Player(Point(9, 6)), None)
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
		scene = game.Scene(RNG(0), [mock_dungeon._MockMiniRogueBuilderUnSettler])
		scene.generate('mini dark rogue')
		scene.enter_actor(mock_dungeon.Player(Point(3, 1)), None)
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
	def should_not_allow_move_player_diagonally_both_from_and_to_good_cell(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockMiniRogueBuilderUnSettler])
		scene.generate('mini rogue lonely')
		scene.enter_actor(mock_dungeon.Player(Point(3, 1)), None)

		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.RIGHT))
		scene.get_player().pos = Point(4, 1)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.DOWN_RIGHT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.DOWN))
		scene.get_player().pos = Point(4, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.RIGHT))
		scene.get_player().pos = Point(5, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.RIGHT))
		scene.get_player().pos = Point(6, 2)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.UP_RIGHT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.RIGHT))
		scene.get_player().pos = Point(7, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.UP))
		scene.get_player().pos = Point(7, 1)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.DOWN_LEFT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.DOWN))
		scene.get_player().pos = Point(7, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.LEFT))
		scene.get_player().pos = Point(6, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.LEFT))
		scene.get_player().pos = Point(5, 2)
		self.assertFalse(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.DOWN_LEFT))
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.LEFT))
		scene.get_player().pos = Point(4, 2)
		self.assertTrue(scene.can_move(scene.get_player(), scene.get_player().pos + game.Direction.DOWN))
		scene.get_player().pos = Point(4, 3)
	def should_leave_scene(self):
		scene = game.Scene(RNG(0), [mock_dungeon._MockMiniRogueBuilderUnSettler])
		scene.generate('mini rogue lonely/1')
		self.assertTrue(scene.one_time())
		player = mock_dungeon.Player(Point(3, 1))
		scene.enter_actor(player, None)
		self.assertEqual(scene.exit_actor(player), player)

class TestAngryMonsters(AbstractTestDungeon):
	def should_angry_move_to_attack_player(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster')
		list(dungeon.process_events(raw=True))

		monster = dungeon.scene.monsters[-1]
		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.scene.monsters[-1].pos, Point(10, 6))
		self.assertEqual(len(dungeon.events), 1)
		self.assertEqual(type(dungeon.events[0]), engine.Events.Move)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].dest, Point(10, 6))
		list(dungeon.process_events(raw=True))

		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(len(dungeon.events), 2)
		self.assertEqual(type(dungeon.events[0]), engine.Events.Attack)
		self.assertEqual(dungeon.events[0].actor, monster)
		self.assertEqual(dungeon.events[0].target, dungeon.get_player())
		self.assertEqual(type(dungeon.events[1]), engine.Events.Health)
		self.assertEqual(dungeon.events[1].target, dungeon.get_player())
		self.assertEqual(dungeon.events[1].diff, -1)
	def should_not_angry_move_when_player_is_out_of_sight(self):
		dungeon = self.dungeon = mock_dungeon.build('close angry monster 2')
		list(dungeon.process_events(raw=True))

		dungeon.scene.monsters[-1].act(dungeon)
		self.assertEqual(dungeon.scene.monsters[-1].pos, Point(4, 4))
		self.assertEqual(len(dungeon.events), 0)
