from clckwrkbdgr import unittest
import textwrap, functools
from clckwrkbdgr.math import Point, Matrix, get_neighbours, Rect, Size
from ..roguedungeon import Item, Wearable
from ..roguedungeon import Scene
from ...engine import events, Events
from ...engine import items, actors, appliances
from ...engine.ui import Sprite

class NanoKey(Item):
	_name = 'nanokey'
	def __init__(self):
		self.value = ''

class Elevator(appliances.LevelPassage):
	_sprite = Sprite('>', None)
	_can_go_down = True
	_unlocking_item = NanoKey
	_id = 'basement'

class Ladder(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_can_go_up = True
	_id = 'roof'

class StealthPistol(Item):
	_attack = 5
	_name = 'stealth pistol'
	_sprite = Sprite('(', None)

class ThermopticCamo(Item, Wearable):
	_name = 'thermoptic camo'
	_protection = 3

class UNATCOAgent(actors.EquippedMonster, actors.Player):
	_attack = 2
	_max_hp = 100
	_max_inventory = 2
	_sprite = Sprite('@', None)

class VacuumCleaner(actors.EquippedMonster):
	_sprite = Sprite('v', None)
	_max_hp = 5

class MJ12Trooper(actors.EquippedMonster):
	_attack = 3
	_max_hp = 200
	_hostile_to = [UNATCOAgent]
	_sprite = Sprite('M', None)

class MockGenerator:
	"""
			####          
			#> +.. ###### 
			#### . #    # 
			     ..+    # 
			       ####+# 
			 ####   ....  
			 # <# ##+#####
			 #  +.+      #
			 #  # ########
			 ####         
			"""
	def build_level(self, result, level_id):
		result.rooms = Matrix((2, 2))
		result.rooms.set_cell((0, 0), Scene.Room((0, 0), (4, 3)))
		result.rooms.set_cell((1, 0), Scene.Room((7, 1), (6, 4)))
		result.rooms.set_cell((0, 1), Scene.Room((1, 5), (4, 5)))
		result.rooms.set_cell((1, 1), Scene.Room((6, 6), (8, 3)))
		result.size = Size(14, 10)
		result.objects = [
				( (Point(1, 1), Elevator('basement', 'top')) ),
				( (Point(3, 6), Ladder('roof', 'roof')) ),
				]
		result.tunnels = [
				Scene.Tunnel(Point(3, 1), Point(7, 3), 'H', 2),
				Scene.Tunnel(Point(11, 4), Point(8, 6), 'V', 1),
				Scene.Tunnel(Point(4, 7), Point(6, 7), 'H', 1),
				]

class TestGridRoomMap(unittest.TestCase):
	def should_find_room_by_pos(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		self.assertEqual(gridmap.room_of(Point(2, 2)), gridmap.rooms.cell((0, 0)))
		self.assertIsNone(gridmap.room_of(Point(10, 0)))
	def should_find_tunnel_by_pos(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		self.assertEqual(gridmap.tunnel_of(Point(5, 1)), gridmap.tunnels[0])
		self.assertIsNone(gridmap.tunnel_of(Point(10, 2)))
	def should_get_tunnels_for_room(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		self.assertEqual(gridmap.get_tunnels(gridmap.rooms.cell((1, 0))), [
			gridmap.tunnels[0], gridmap.tunnels[1],
			])
	def should_get_rooms_for_tunnel(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		self.assertEqual(list(gridmap.get_tunnel_rooms(gridmap.tunnels[0])), [
			gridmap.rooms.cell((0, 0)),
			gridmap.rooms.cell((1, 0)),
			])
	def should_move_within_terrain(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')
		player = scene.get_player()
		mj12 = MJ12Trooper(None)
		gridmap.monsters.append(mj12)

		self.assertFalse(gridmap.can_move(player, Point(0, 0)))
		self.assertFalse(gridmap.can_move(player, Point(1, 0)))
		self.assertFalse(gridmap.can_move(player, Point(0, 1)))
		self.assertTrue(gridmap.can_move(player, Point(1, 1)))
		self.assertFalse(gridmap.can_move(player, Point(1, 2)))
		self.assertTrue(gridmap.can_move(player, Point(2, 1)))
		self.assertTrue(gridmap.can_move(mj12, Point(3, 1)))
		self.assertFalse(gridmap.can_move(player, Point(3, 1)))
		self.assertTrue(gridmap.can_move(player, Point(2, 1)))
		self.assertFalse(gridmap.can_move(mj12, Point(4, 1)))
		player.pos = Point(4, 2)
		self.assertTrue(gridmap.can_move(player, Point(4, 1)))
		self.assertTrue(gridmap.can_move(player, Point(5, 2)))
		player.pos = Point(4, 1)
		self.assertFalse(gridmap.can_move(player, Point(5, 2)))
		self.assertTrue(gridmap.can_move(player, Point(5, 1)))
		player.pos = Point(8, 2)
		self.assertFalse(gridmap.can_move(player, Point(7, 3)))
	def should_detect_player_amongst_other_actors(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')

		mj12 = MJ12Trooper(Point(9, 2))
		gridmap.monsters.append(mj12)

		self.assertEqual(list(scene.iter_actors_at(Point(9, 2))), [mj12])
		self.assertEqual(list(scene.iter_actors_at(Point(1, 1), with_player=True)), [scene.get_player()])
	def should_rip_monster(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')

		pistol = StealthPistol()
		armor = ThermopticCamo()

		mj12 = MJ12Trooper(None)
		mj12.inventory.append(pistol)
		mj12.inventory.append(armor)

		mj12.pos = Point(9, 2)
		gridmap.monsters.append(mj12)
		loot = list(scene.rip(mj12))
		self.assertEqual(loot, [armor, pistol])
		self.assertEqual(list(scene.iter_actors_at(Point(9, 2))), [])
	def should_drop_and_grab_item(self):
		gridmap = scene = Scene(MockGenerator())
		scene.generate('top')
		key = NanoKey()
		gridmap.drop_item(items.ItemAtPos(Point(1, 1), key))
		self.assertEqual(list(scene.iter_items_at(Point(1, 1))), [key])

		self.assertEqual(scene.take_item(items.ItemAtPos((1, 1), key)), key)
		self.assertEqual(list(scene.iter_items_at(Point(1, 1))), [])

class TestDungeon(unittest.TestCase):
	def should_iter_dungeon_cells(self):
		scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')
		vision = scene.make_vision()
		scene.get_player().pos = Point(3, 1)
		list(vision.visit(scene.get_player()))
		scene.get_player().pos = Point(5, 1)
		list(vision.visit(scene.get_player()))
		scene.get_player().pos = Point(5, 3)
		list(vision.visit(scene.get_player()))
		scene.get_player().pos = Point(7, 3)
		list(vision.visit(scene.get_player()))

		mj12 = MJ12Trooper(None)
		mj12.pos = Point(8, 3)
		scene.monsters.append(mj12)
		pistol = StealthPistol()
		scene.items.append((Point(9, 2), pistol))

		view = Matrix((15, 10), '_')
		visible = Matrix((15, 10), '.')
		visited = Matrix((15, 10), '.')
		for pos, (terrain, objects, items, monsters) in scene.iter_cells(None):
			if vision.is_visible(pos):
				visible.set_cell(pos, '*')
			if vision.is_explored(pos):
				visited.set_cell(pos, '*')
			if monsters:
				view.set_cell(pos, monsters[-1].sprite.sprite)
			elif items:
				view.set_cell(pos, items[-1].sprite.sprite)
			elif objects:
				view.set_cell(pos, objects[-1].sprite.sprite)
			else:
				view.set_cell(pos, terrain.sprite.sprite)
		self.maxDiff = None
		self.assertEqual(view.tostring(), textwrap.dedent("""\
				+--+___________
				|>.+##_+----+__
				+--+_#_|.(..|__
				_____##@M...|__
				_______+---++__
				_+--++__####___
				_|.<|_+-+----+_
				_|..+#+......|_
				_|..|_+------+_
				_+--+__________
				"""))
		self.assertEqual(visible.tostring(), textwrap.dedent("""\
				...............
				...***.******..
				.....*.******..
				.....********..
				.......******..
				...............
				...............
				...............
				...............
				...............
				""").replace('_', ' '))
		self.assertEqual(visited.tostring(), textwrap.dedent("""\
				****...........
				******.******..
				****.*.******..
				.....********..
				.......******..
				...............
				...............
				...............
				...............
				...............
				""").replace('_', ' '))
	def should_locate_in_maze(self):
		scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')

		scene.get_player().pos = Point(1, 1)
		self.assertEqual(scene.current_room, scene.rooms.cell((0, 0)))
		self.assertIsNone(scene.current_tunnel)

		scene.get_player().pos = Point(3, 1)
		self.assertEqual(scene.current_room, scene.rooms.cell((0, 0)))
		self.assertEqual(scene.current_tunnel, scene.tunnels[0])

		scene.get_player().pos = Point(5, 1)
		self.assertIsNone(scene.current_room)
		self.assertEqual(scene.current_tunnel, scene.tunnels[0])
	def should_detect_player_by_monsters(self):
		scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')
		scene.get_player().pos = Point(9, 3)

		mj12 = MJ12Trooper(None)
		mj12.pos = Point(8, 3)
		scene.monsters.append(mj12)

		vacuum = VacuumCleaner(None)
		vacuum.pos = Point(2, 1)
		scene.monsters.append(vacuum)

		self.assertTrue(scene.actor_sees_player(mj12))
		self.assertFalse(scene.actor_sees_player(vacuum))
	def should_iter_monsters_in_rect(self):
		scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')
		scene.get_player().pos = Point(9, 3)

		mj12 = MJ12Trooper(None)
		mj12.pos = Point(8, 3)
		scene.monsters.append(mj12)

		vacuum = VacuumCleaner(None)
		vacuum.pos = Point(2, 1)
		scene.monsters.append(vacuum)

		self.assertEqual(list(scene.iter_actors_in_rect(
			Rect((8, 2), Size(3, 3))
			)), scene.monsters[:2])
	def should_treat_all_monsters_as_active(self):
		scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')
		self.assertEqual(list(scene.iter_active_monsters()), list(scene.monsters))
	def should_enter_and_exit_actor(self):
		scene = Scene(MockGenerator())
		scene.generate('top')
		scene.enter_actor(UNATCOAgent(None), 'basement')
		self.assertTrue(scene.get_player())
		scene.exit_actor(scene.get_player())
		self.assertFalse(scene.get_player())
