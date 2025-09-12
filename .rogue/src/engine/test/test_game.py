from clckwrkbdgr import unittest
import clckwrkbdgr.serialize.stream as savefile
from .. import _base
from .. import events
from .. import mock
from ..mock import *
from .utils import *

class TestEvents(unittest.TestCase):
	def should_process_events(self):
		game = _base.Game()
		game.fire_event(DropItem(who='me', where='floor', what='something'))
		self.assertEqual(list(game.process_events()), [
			'me drops something on floor',
			])

class TestSerialization(AbstractTestDungeon):
	def should_load_game_or_start_new_one(self):
		game = self.game
		self.assertEqual(game.scene.monsters[0].pos, Point(3, 8))
		game.scene.monsters[0].pos = Point(2, 2)
		writer = savefile.Writer(MockWriterStream(), 1)
		game.save(writer)
		dump = writer.f.dump

		reader = savefile.Reader(iter(dump))
		restored = NanoDungeon()
		restored.load(reader)

		self.assertEqual(restored.scene.monsters[0].pos, Point(2, 2))

		restored = NanoDungeon()
		restored.generate('floor')
		self.assertEqual(restored.scene.monsters[0].pos, Point(3, 8))
	def should_serialize_and_deserialize_game(self):
		dungeon = self.game
		writer = savefile.Writer(MockWriterStream(), 1)
		dungeon.save(writer)
		dump = writer.f.dump[1:]
		Wall = mock.Wall.__name__
		Floor = mock.Floor.__name__
		ToxicWaste = mock.ToxicWaste.__name__
		#self.maxDiff = None
		self.assertEqual(dump, list(map(str, [0, 1521280756,
			'floor', 'floor',
			10, 10,
			Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Wall, Floor, ToxicWaste, 0, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Floor, Wall,
			Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall, Wall,
			2,
				'Butterfly', 3, 8, 'red',
				'Rogue', 1, 5, 10, 1, 'Dagger', '0', '0',
			1,
				'ScribbledNote', 'welcome', 1, 2,
			3,
				'StairsUp', None, None, 1, 5,
				'Statue', 'goddess', 3, 2,
				'StairsDown', 'tomb', 'enter', 4, 6,
			'',

			'floor',
			10, 10,
			0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
			0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
			0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
			1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
			1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
			1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
			1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
			1, 1, 1, 1, 0, 0, 0, 0, 0, 0,
			0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
			0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
			'',
			])))
		dump = [str(1)] + list(map(str, dump))

		restored_dungeon = NanoDungeon()
		reader = savefile.Reader(iter(dump))
		restored_dungeon.load(reader)
		self.assertEqual(
				[(_.name, _.pos) for _ in dungeon.scene.monsters],
				[(_.name, _.pos) for _ in restored_dungeon.scene.monsters],
				)
		self.assertEqual(dungeon.scene.appliances[0].pos, restored_dungeon.scene.appliances[0].pos)
		for pos in dungeon.scene.cells.size.iter_points():
			self.assertEqual(type(dungeon.scene.cells.cell(pos)).__name__, type(restored_dungeon.scene.cells.cell(pos)).__name__, str(pos))
			self.assertEqual(dungeon.scene.cells.cell(pos).passable, restored_dungeon.scene.cells.cell(pos).passable, str(pos))
			self.assertEqual(dungeon.vision.visited.cell(pos), restored_dungeon.vision.visited.cell(pos), str(pos))
		self.assertEqual(len(dungeon.scene.monsters), len(restored_dungeon.scene.monsters))
		for monster, restored_monster in zip(dungeon.scene.monsters, restored_dungeon.scene.monsters):
			self.assertEqual(monster.name, restored_monster.name)
			self.assertEqual(monster.pos, restored_monster.pos)
		self.assertEqual(len(dungeon.scene.items), len(restored_dungeon.scene.items))
		for item, restored_item in zip(dungeon.scene.items, restored_dungeon.scene.items):
			self.assertEqual(item.item.name, restored_item.item.name)
			self.assertEqual(item.pos, restored_item.pos)

class TestActionLoop(AbstractTestDungeon):
	def should_process_others(self):
		game = self.game
		self.assertFalse(game.scene.get_player().has_acted())
		game.process_others()
		self.assertEqual(game.playing_time, 0)
		self.assertEqual(list(game.process_events()), [])

		game.scene.get_player().spend_action_points()
		self.assertTrue(game.scene.get_player().has_acted())
		game.process_others()
		self.assertEqual(game.playing_time, 1)
		self.assertFalse(game.scene.get_player().has_acted())
		self.assertEqual(list(game.process_events()), [
			'butterfly flops its wings',
			])

class TestVision(AbstractTestDungeon):
	def should_see_places(self):
		game = self.game
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size), visited=False), unittest.dedent("""\
				__________
				__________
				__________
				#...______
				#...______
				#@..______
				##.~______
				#...______
				__________
				__________
				""").replace('_', ' '))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size), visited=False), unittest.dedent("""\
				__________
				__________
				__________
				__________
				__________
				__________
				__.~>..___
				__.....___
				__.b@..___
				__#####___
				""").replace('_', ' '))
	def should_remember_places(self):
		game = self.game
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				__________
				__________
				__________
				#...______
				#...______
				#@..______
				##.~______
				#...______
				__________
				__________
				""").replace('_', ' '))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertEqual(game.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				__________
				__________
				__________
				#   ______
				#    _____
				#<    ____
				##.~>..___
				# .....___
				# .b@..___
				_######___
				""").replace('_', ' '))

class TestActions(AbstractTestDungeon):
	def should_suicide(self):
		game = self.game
		game.suicide(game.scene.get_player())
		self.assertTrue(game.is_finished())

class TestMovement(AbstractTestDungeon):
	def should_wait_in_place(self):
		game = self.game
		game.wait(game.scene.get_player())
		self.assertTrue(game.scene.get_player().has_acted())
	def should_move_actor(self):
		game = self.game
		butterfly = next(game.scene.iter_actors_at(Point(3, 8)))
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(1, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [
			_base.Events.Move(game.scene.get_player(), Point(2, 6)),
			_base.Events.Discover(butterfly),
			])

		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#<.......#
				##@~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_not_move_into_void(self):
		game = self.game
		game.jump_to(game.scene.get_player(), Point(0, 6))
		self.assertFalse(game.move_actor(game.scene.get_player(), Point(-1, 0)))
		self.assertFalse(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.StareIntoVoid()])
	def should_walk_through_terrain_in_noclip_mode(self):
		game = self.game
		butterfly = next(game.scene.iter_actors_at(Point(3, 8)))
		game.god.noclip = True

		self.assertTrue(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [
			_base.Events.Move(game.scene.get_player(), Point(1, 6)),
			_base.Events.Discover(butterfly),
			])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#<.......#
				#@.~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_bump_into_terrain(self):
		game = self.game
		self.assertFalse(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.BumpIntoTerrain(game.scene.get_player(), Point(1, 6))])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#@.......#
				##.~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_attack_other_actor(self):
		game = self.game
		game.scene.transfer_actor(game.scene.get_player(), Point(3, 7))
		self.assertFalse(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(game.events, [_base.Events.BumpIntoActor(game.scene.get_player(), next(_ for _ in game.scene.monsters if _.name == 'butterfly'))])
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#<.......#
				##.~>....#
				#..@.....#
				#..b.....#
				##########
				"""))

class TestItems(AbstractTestDungeon):
	def should_drop_item(self):
		game = self.game
		dagger = game.scene.get_player().inventory[0]
		game.drop_item(game.scene.get_player(), dagger)
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(list(game.scene.iter_items_at((1, 5))), [dagger])
		self.assertFalse(game.scene.get_player().inventory)
		self.assertEqual(game.events, [_base.Events.DropItem(game.scene.get_player(), dagger)])
		game.jump_to(game.scene.get_player(), Point(2, 6))
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#?.&.....#
				#........#
				#........#
				#(.......#
				##@~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_grab_item(self):
		game = self.game

		game.grab_item_here(game.scene.get_player())
		self.assertEqual(game.events, [_base.Events.NothingToPickUp()])
		self.assertFalse(game.scene.get_player().has_acted())

		list(game.process_events(raw=True)) # Clear events.
		game.jump_to(game.scene.get_player(), Point(1, 2))
		game.grab_item_here(game.scene.get_player())
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertEqual(list(game.scene.iter_items_at((1, 5))), [])
		scroll = game.scene.get_player().find_item(ScribbledNote)
		self.assertIsNotNone(scroll)
		self.assertEqual(game.events, [_base.Events.GrabItem(game.scene.get_player(), scroll)])
		game.jump_to(game.scene.get_player(), Point(2, 2))
		self.assertEqual(game.scene.tostring(Rect((0, 0), game.scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#.@&.....#
				#........#
				#........#
				#<.......#
				##.~>....#
				#........#
				#..b.....#
				##########
				"""))
	def should_not_exceed_inventory_size(self):
		game = self.game
		game.scene.get_player()._max_inventory = 1
		game.jump_to(game.scene.get_player(), Point(1, 2))
		game.grab_item_here(game.scene.get_player())
		self.assertFalse(game.scene.get_player().has_acted())
		scroll = next(game.scene.iter_items_at((1, 2)))
		self.assertTrue(scroll)
		self.assertIsNone(game.scene.get_player().find_item(ScribbledNote))
		self.assertEqual(game.events, [_base.Events.InventoryIsFull(scroll)])
	def should_consume_items(self):
		game = self.game
		game.scene.get_player().hp -= 5
		game.scene.get_player().inventory.append(Potion())
		dagger, potion = game.scene.get_player().inventory

		game.consume_item(game.scene.get_player(), dagger)
		self.assertEqual(game.events, [_base.Events.NotConsumable(dagger)])
		self.assertFalse(game.scene.get_player().has_acted())

		list(game.process_events(raw=True)) # Clear events.
		game.consume_item(game.scene.get_player(), potion)
		self.assertEqual(game.events, [
			_base.Events.ConsumeItem(game.scene.get_player(), potion),
			Healed(game.scene.get_player(), +5),
			])
		self.assertTrue(game.scene.get_player().has_acted())
		self.assertFalse(game.scene.get_player().find_item(Potion))
		self.assertEqual(game.scene.get_player().hp, 10)
	def should_wield_items(self):
		game = self.game
		game.scene.get_player().inventory.append(Potion())
		dagger, potion = game.scene.get_player().inventory

		game.unwield_item(game.scene.get_player())
		self.assertEqual(game.events, [_base.Events.NotWielding()])
		self.assertFalse(game.scene.get_player().has_acted())

		list(game.process_events(raw=True)) # Clear events.
		game.wield_item(game.scene.get_player(), dagger)
		self.assertEqual(game.events, [_base.Events.Wield(game.scene.get_player(), dagger)])
		self.assertTrue(game.scene.get_player().has_acted())

		game.scene.get_player().add_action_points()
		list(game.process_events(raw=True)) # Clear events.
		game.wield_item(game.scene.get_player(), potion)
		self.assertEqual(game.events, [
			_base.Events.Unwield(game.scene.get_player(), dagger),
			_base.Events.Wield(game.scene.get_player(), potion),
			])
		self.assertTrue(game.scene.get_player().has_acted())

		game.scene.get_player().add_action_points()
		list(game.process_events(raw=True)) # Clear events.
		game.unwield_item(game.scene.get_player())
		self.assertEqual(game.events, [
			_base.Events.Unwield(game.scene.get_player(), potion),
			])
		self.assertTrue(game.scene.get_player().has_acted())
	def should_wear_items(self):
		game = self.game
		game.scene.get_player().inventory.append(Rags())
		game.scene.get_player().inventory.append(ChainMail())
		dagger, rags, armor = game.scene.get_player().inventory

		game.take_off_item(game.scene.get_player())
		self.assertEqual(game.events, [_base.Events.NotWearing()])
		self.assertFalse(game.scene.get_player().has_acted())

		list(game.process_events(raw=True)) # Clear events.
		game.wear_item(game.scene.get_player(), dagger)
		self.assertEqual(game.events, [_base.Events.NotWearable(dagger)])
		self.assertFalse(game.scene.get_player().has_acted())

		list(game.process_events(raw=True)) # Clear events.
		game.wear_item(game.scene.get_player(), rags)
		self.assertEqual(game.events, [_base.Events.Wear(game.scene.get_player(), rags)])
		self.assertTrue(game.scene.get_player().has_acted())

		game.scene.get_player().add_action_points()
		list(game.process_events(raw=True)) # Clear events.
		game.wear_item(game.scene.get_player(), armor)
		self.assertEqual(game.events, [
			_base.Events.TakeOff(game.scene.get_player(), rags),
			_base.Events.Wear(game.scene.get_player(), armor),
			])
		self.assertTrue(game.scene.get_player().has_acted())

		game.scene.get_player().add_action_points()
		list(game.process_events(raw=True)) # Clear events.
		game.take_off_item(game.scene.get_player())
		self.assertEqual(game.events, [
			_base.Events.TakeOff(game.scene.get_player(), armor),
			])
		self.assertTrue(game.scene.get_player().has_acted())

class TestChat(AbstractTestDungeon):
	def should_not_chat_with_empty_space(self):
		self.assertEqual(self.game.get_respondents(self.game.scene.get_player()), [])
		self.assertEqual(self.game.events, [_base.Events.NoOneToChat()])
	def should_pick_respondents(self):
		smith = Smith(self.game.scene.get_player().pos + Point(1, 0))
		self.game.scene.enter_actor(smith, None)
		self.assertEqual(self.game.get_respondents(self.game.scene.get_player()), [smith])
		self.assertEqual(self.game.events, [])
	def should_chat_in_direction(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		smith.pos = game.scene.get_player().pos + Point(1, 0)
		prompt, on_yes, on_no = game.chat(game.scene.get_player(), Point(1, 0))
		self.assertEqual(prompt, "Bring me gold, I'll give you a chain mail.")
	def should_refuse_to_chat_with_no_one_in_direction(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		smith.pos = game.scene.get_player().pos + Point(1, 1)
		prompt, on_yes, on_no = game.chat(game.scene.get_player(), Point(1, 0))
		self.assertIsNone(prompt)
		self.assertEqual(self.game.events, [_base.Events.NoOneToChatInDirection()])

	def should_decline_quests_from_npc(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		prompt, on_yes, on_no = game.chat(game.scene.get_player(), smith)
		self.assertEqual(prompt, "Bring me gold, I'll give you a chain mail.")
		on_no()
		self.assertFalse(smith.quest.is_active())
		self.assertEqual(game.events, [_base.Events.ChatComeLater()])
	def should_accept_quests_from_npc(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		prompt, on_yes, on_no = game.chat(game.scene.get_player(), smith)
		self.assertEqual(prompt, "Bring me gold, I'll give you a chain mail.")
		on_yes()
		self.assertTrue(smith.quest.is_active())
		self.assertEqual(game.events, [])
	def should_decline_quests_if_full(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		smith.prepare_chat(game)
		smith.quest.activate()

		other_smith = Smith(game.scene.get_player().pos + Point(1, 1))

		prompt, on_yes, on_no = game.chat(game.scene.get_player(), other_smith)
		self.assertIsNone(prompt)
		self.assertIsNone(other_smith.quest)
		self.assertEqual(game.events, [_base.Events.TooMuchQuests()])
		self.assertEqual(len(list(game.scene.iter_active_quests())), 1)
	def should_remind_about_not_finished_quest(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		smith.prepare_chat(game)
		smith.quest.activate()

		self.assertEqual(smith.quest.summary(), "Bring Smith a piece of gold.")

		prompt, on_yes, on_no = game.chat(game.scene.get_player(), smith)
		self.assertIsNone(prompt)
		self.assertTrue(smith.quest.is_active())
		self.assertEqual(game.events, [_base.Events.ChatQuestReminder("Gold. I need gold.")])
	def should_decline_completing_finished_quest(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		smith.prepare_chat(game)
		smith.quest.activate()

		game.scene.get_player().grab(Gold())

		prompt, on_yes, on_no = game.chat(game.scene.get_player(), smith)
		self.assertEqual(prompt, "Will trade this chain mail for your gold.")
		on_no()
		self.assertTrue(smith.quest.is_active())
		self.assertEqual(game.events, [_base.Events.ChatComeLater()])
	def should_accept_completing_finished_quest(self):
		game = self.game
		smith = Smith(game.scene.get_player().pos + Point(1, 0))
		game.scene.enter_actor(smith, None)
		smith.prepare_chat(game)
		smith.quest.activate()

		game.scene.get_player().grab(Gold())

		prompt, on_yes, on_no = game.chat(game.scene.get_player(), smith)
		self.assertEqual(prompt, "Will trade this chain mail for your gold.")
		on_yes()
		self.assertIsNone(smith.quest)
		self.assertEqual(game.events, [_base.Events.ChatThanks()])

class TestScenes(AbstractTestDungeon):
	def should_travel_to_other_scene(self):
		game = self.game
		self.assertEqual(len(game.scenes), 1)

		game.travel(game.scene.get_player(), 'tomb', 'enter')
		self.assertEqual(game.current_scene_id, 'tomb')
		self.assertEqual(len(game.scenes), 2)
		self.assertEqual(game.scene.get_player().pos, Point(1, 1))
	def should_descend_and_ascend(self):
		game = self.game
		self.assertEqual(len(game.scenes), 1)
		butterfly = next(game.scene.iter_actors_at(Point(3, 8)))

		self.assertFalse(game.descend(game.scene.get_player()))
		self.assertEqual(game.events, [
			_base.Events.CannotDescend(game.scene.get_player().pos),
			])

		list(game.process_events(raw=True)) # Clear events.
		game.jump_to(game.scene.get_player(), Point(4, 6))
		self.assertTrue(game.descend(game.scene.get_player()))
		self.assertEqual(game.events, [
			_base.Events.Discover(butterfly),
			_base.Events.Descend(game.scene.get_player()),
			])
		self.assertEqual(game.current_scene_id, 'tomb')
		self.assertEqual(len(game.scenes), 2)
		self.assertEqual(game.scene.get_player().pos, Point(1, 1))

		list(game.process_events(raw=True)) # Clear events.
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(0, 1)))
		self.assertFalse(game.ascend(game.scene.get_player()))
		self.assertEqual(game.events, [
			_base.Events.Move(game.scene.get_player(), game.scene.get_player().pos),
			_base.Events.CannotAscend(game.scene.get_player().pos),
			])

		list(game.process_events(raw=True)) # Clear events.
		self.assertTrue(game.move_actor(game.scene.get_player(), Point(0, -1)))
		self.assertFalse(game.ascend(game.scene.get_player()))
		self.assertEqual(game.events, [
			_base.Events.Move(game.scene.get_player(), game.scene.get_player().pos),
			_base.Events.NeedKey(Gold),
			])
		self.assertEqual(game.current_scene_id, 'tomb')

		list(game.process_events(raw=True)) # Clear events.
		game.scene.get_player().grab(Gold())
		self.assertTrue(game.ascend(game.scene.get_player()))
		self.assertEqual(game.events, [
			_base.Events.Ascend(game.scene.get_player()),
			])
		self.assertEqual(game.current_scene_id, 'floor')
		self.assertEqual(len(game.scenes), 2)
		self.assertEqual(game.scene.get_player().pos, Point(4, 6))
