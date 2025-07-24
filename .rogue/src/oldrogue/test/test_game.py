from clckwrkbdgr import unittest
import textwrap, functools
from clckwrkbdgr.math import Point, Matrix, get_neighbours
from .. import game
from ..game import Item, Wearable, LevelPassage
from ..game import Player
from ..game import Scene, Dungeon
from ...engine import events
from ...engine import items, actors

class Elevator(LevelPassage):
	_sprite = '>'
	_can_go_down = True
	_id = 'basement'

class Ladder(LevelPassage):
	_sprite = '<'
	_can_go_up = True
	_id = 'roof'

class NanoKey(Item):
	def __init__(self):
		self.value = ''

class StealthPistol(Item):
	_attack = 5
	_sprite = '('

class ThermopticCamo(Item, Wearable):
	_protection = 3

class HazmatSuit(Item, Wearable):
	_protection = 1

class StimPack(Item, items.Consumable):
	def consume(self, monster):
		monster.affect_health(25)
		return []

class SmartStimPack(Item, items.Consumable):
	def consume(self, monster):
		if monster.hp >= monster.max_hp:
			return []
		else: # pragma: no cover
			raise RuntimeError("Should never reach here.")

class UNATCOAgent(Player):
	_attack = 2
	_max_hp = 100
	_max_inventory = 2
	_sprite = '@'

class VacuumCleaner(actors.EquippedMonster):
	_max_hp = 5

class NSFTerrorist(actors.EquippedMonster):
	_attack = 1
	_max_hp = 50

class MJ12Trooper(actors.EquippedMonster):
	_attack = 3
	_max_hp = 200
	_hostile_to = [UNATCOAgent, NSFTerrorist]
	_sprite = 'M'

class TestUtils(unittest.TestCase):
	def should_detect_diagonal_movement(self):
		self.assertTrue(game.is_diagonal_movement(Point(0, 0), Point(1, 1)))
		self.assertTrue(game.is_diagonal_movement(Point(0, 0), Point(1, -1)))
		self.assertFalse(game.is_diagonal_movement(Point(0, 0), Point(1, 0)))
		self.assertFalse(game.is_diagonal_movement(Point(0, 0), Point(0, 1)))

class TestMonster(unittest.TestCase):
	class UNATCO(game.Dungeon):
		GENERATOR = lambda *_:None
		PLAYER_TYPE = UNATCOAgent
	def should_consumeItems(self):
		dungeon = self.UNATCO()

		key = NanoKey()
		key.value = '0451'
		stimpack = StimPack()
		smart_stimpack = SmartStimPack()

		jc = UNATCOAgent(None)
		jc.inventory.append(key)
		jc.inventory.append(stimpack)
		jc.inventory.append(smart_stimpack)

		self.assertEqual(_R(dungeon.consume_item(jc, key)), _R([
			game.Event.NotConsumable(key),
			]))
		self.assertTrue(jc.has_item(NanoKey))

		self.assertEqual(_R(dungeon.consume_item(jc, stimpack)), _R([
			game.Event.MonsterConsumedItem(jc, stimpack),
			]))
		self.assertFalse(jc.has_item(StimPack))
		self.assertEqual(jc.hp, jc.max_hp)

		self.assertEqual(_R(dungeon.consume_item(jc, smart_stimpack)), _R([
			game.Event.MonsterConsumedItem(jc, smart_stimpack),
			]))
		self.assertFalse(jc.has_item(SmartStimPack))

class MockGenerator:
	MAIN_LEVEL = textwrap.dedent("""\
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
			""")
	ROOF = textwrap.dedent("""\
			##############
			#=           #
			#            #
			#            #
			#            #
			#            #
			#            #
			#            #
			#            #
			##############
			""")
	def build_level(self, level_id):
		result = Scene()
		if level_id == 'top':
			result.rooms, result.tunnels[:], result.objects[:] = self._parse_layout(self.MAIN_LEVEL)
		elif level_id == 'roof':
			result.rooms, result.tunnels[:], result.objects[:] = self._parse_layout(self.ROOF)
		return result
	@functools.lru_cache()
	def _parse_layout(self, layout):
		layout = Matrix.fromstring(layout)

		rects = []
		for x in range(layout.width):
			for y in range(layout.height):
				if layout.cell( (x, y) ) != '#':
					continue
				if not layout.valid( (x+1, y) ):
					continue
				if not layout.valid( (x, y+1) ):
					continue
				if layout.cell( (x+1, y) ) not in '#+' or layout.cell( (x, y+1) ) not in '#+':
					continue
				right = min([_ for _ in range(x, layout.width) if layout.cell((_, y)) not in '#+'] + [layout.width])
				bottom = min([_ for _ in range(y, layout.height) if layout.cell((x, _)) not in '#+'] + [layout.height])
				rects.append( ((x, y), (right-x, bottom-y)) )

		rects = sorted(rects, key=lambda rect: (rect[0][1], rect[0][0]))
		if len(rects) == 4:
			rooms = Matrix((2, 2))
			rooms.set_cell((0, 0), Scene.Room(*(rects[0])))
			rooms.set_cell((1, 0), Scene.Room(*(rects[1])))
			rooms.set_cell((0, 1), Scene.Room(*(rects[2])))
			rooms.set_cell((1, 1), Scene.Room(*(rects[3])))
		else:
			rooms = Matrix((1, 1))
			rooms.set_cell((0, 0), Scene.Room(*(rects[0])))

		tunnels = []
		for y in range(layout.height):
			for x in range(layout.width):
				if layout.cell( (x, y) ) != '+':
					continue
				if any(tunnel.contains( (x, y) ) for tunnel in tunnels):
					continue
				current = Point(x, y)
				path = [current]
				for _ in range(layout.width * layout.height):
					neighs = get_neighbours(layout, current, check=lambda p: p in '.+')
					neighs = [p for p in neighs if p not in path]
					if not neighs:
						break
					current, = neighs
					path.append(current)
				direction = ''
				bending = 0
				for prev, current in zip(path, path[1:]):
					h, v = abs(prev.x - current.x), abs(prev.y - current.y)
					if not direction:
						direction = 'H' if h > v else 'V'
					elif not bending:
						if (direction == 'H') != (h > v):
							bending = max(
									abs(current.x - path[0].x),
									abs(current.y - path[0].y),
									)
				tunnels.append(Scene.Tunnel(path[0], path[-1], direction, bending or 1))

		objects = []
		for y in range(layout.height):
			for x in range(layout.width):
				if layout.cell( (x, y) ) == '>':
					objects.append( (Point(x, y), Elevator(None, None)) )
				elif layout.cell( (x, y) ) == '<':
					objects.append( (Point(x, y), Ladder('roof', 'roof')) )
				elif layout.cell( (x, y) ) == '=':
					objects.append( (Point(x, y), Ladder('top', 'roof')) )

		return rooms, tunnels, objects

def _R(events): return list(map(repr, events))

class TestGridRoomMap(unittest.TestCase):
	class UNATCO(game.Dungeon):
		GENERATOR = MockGenerator
		PLAYER_TYPE = UNATCOAgent
	def _map(self):
		return MockGenerator().build_level('top')
	def should_parse_layout_correctly(self):
		gridmap = self._map()
		result = Matrix.fromstring(MockGenerator.MAIN_LEVEL)
		result.clear(' ')
		for room in gridmap.rooms.values():
			for x in range(room.left, room.right + 1):
				result.set_cell( (x, room.top), '#')
				result.set_cell( (x, room.bottom), '#')
			for y in range(room.top, room.bottom + 1):
				result.set_cell( (room.left, y), '#')
				result.set_cell( (room.right, y), '#')
		for tunnel in gridmap.tunnels:
			cells = list(tunnel.iter_points())
			for cell in cells:
				result.set_cell(cell, '.')
			result.set_cell(cells[0], '+')
			result.set_cell(cells[-1], '+')
		for pos, obj in gridmap.objects:
			result.set_cell(pos, obj.sprite)
		self.assertEqual(result.tostring(), MockGenerator.MAIN_LEVEL)
	def should_find_room_by_pos(self):
		gridmap = self._map()
		self.assertEqual(gridmap.room_of(Point(2, 2)), gridmap.rooms.cell((0, 0)))
		self.assertIsNone(gridmap.room_of(Point(10, 0)))
	def should_find_tunnel_by_pos(self):
		gridmap = self._map()
		self.assertEqual(gridmap.tunnel_of(Point(5, 1)), gridmap.tunnels[0])
		self.assertIsNone(gridmap.tunnel_of(Point(10, 2)))
	def should_get_tunnels_for_room(self):
		gridmap = self._map()
		self.assertEqual(gridmap.get_tunnels(gridmap.rooms.cell((1, 0))), [
			gridmap.tunnels[0], gridmap.tunnels[1],
			])
	def should_get_rooms_for_tunnel(self):
		gridmap = self._map()
		self.assertEqual(list(gridmap.get_tunnel_rooms(gridmap.tunnels[0])), [
			gridmap.rooms.cell((0, 0)),
			gridmap.rooms.cell((1, 0)),
			])
	def should_move_within_terrain(self):
		gridmap = self._map()
		self.assertFalse(gridmap.can_move_to(Point(0, 0)))
		self.assertFalse(gridmap.can_move_to(Point(1, 0)))
		self.assertFalse(gridmap.can_move_to(Point(0, 1)))
		self.assertTrue(gridmap.can_move_to(Point(1, 1)))
		self.assertFalse(gridmap.can_move_to(Point(1, 2)))
		self.assertTrue(gridmap.can_move_to(Point(2, 1)))
		self.assertTrue(gridmap.can_move_to(Point(3, 1), with_tunnels=False))
		self.assertTrue(gridmap.can_move_to(Point(3, 1), with_tunnels=True))
		self.assertTrue(gridmap.can_move_to(Point(2, 1), with_tunnels=True))
		self.assertFalse(gridmap.can_move_to(Point(4, 1), with_tunnels=False))
		self.assertTrue(gridmap.can_move_to(Point(4, 1), with_tunnels=True))
		self.assertTrue(gridmap.can_move_to(Point(5, 2), with_tunnels=True))
		self.assertFalse(gridmap.can_move_to(Point(5, 2), with_tunnels=True, from_pos=Point(4, 1)))
		self.assertTrue(gridmap.can_move_to(Point(5, 1), with_tunnels=True))
		self.assertFalse(gridmap.can_move_to(Point(7, 3), with_tunnels=True, from_pos=Point(8, 2)))
	def should_detect_objects_on_map(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')

		mj12 = MJ12Trooper(None)
		pistol = StealthPistol()
		armor = ThermopticCamo()

		gridmap = dungeon.scene
		gridmap.items.append( (Point(1, 1), pistol) )
		gridmap.items.append( (Point(1, 1), armor) )
		mj12.pos = Point(9, 2)
		gridmap.monsters.append(mj12)

		elevator = gridmap.objects[0][1]

		self.assertEqual(list(dungeon.scene.iter_items_at(Point(2, 1))), [])
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [armor, pistol])
		self.assertEqual(list(dungeon.scene.iter_appliances_at(Point(1, 2))), [])
		self.assertEqual(list(dungeon.scene.iter_appliances_at(Point(1, 1))), [elevator])
		self.assertEqual(list(dungeon.scene.iter_actors_at(Point(9, 2))), [mj12])
	def should_rip_monster(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')

		pistol = StealthPistol()
		armor = ThermopticCamo()

		mj12 = MJ12Trooper(None)
		mj12.inventory.append(pistol)
		mj12.inventory.append(armor)

		gridmap = dungeon.scene
		mj12.pos = Point(9, 2)
		gridmap.monsters.append(mj12)
		self.assertTrue(mj12.is_alive())
		with self.assertRaises(RuntimeError):
			list(dungeon.rip(mj12))
		self.assertTrue(mj12.is_alive())
		self.assertEqual(list(dungeon.scene.iter_actors_at(Point(9, 2))), [mj12])

		mj12.hp = 0
		loot = list(dungeon.rip(mj12))
		self.assertEqual(loot, [armor, pistol])
		self.assertEqual(list(dungeon.scene.iter_actors_at(Point(9, 2))), [])
	def should_grab_item(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')

		pistol = StealthPistol()
		armor = ThermopticCamo()

		jc = UNATCOAgent(None)

		gridmap = dungeon.scene
		key = NanoKey()
		gridmap.items.append( (Point(1, 1), key) )
		gridmap.items.append( (Point(1, 1), pistol) )
		gridmap.items.append( (Point(1, 1), armor) )
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [armor, pistol, key])

		events = dungeon.grab_item(jc, key)
		self.assertEqual(_R(events), _R([game.Event.GrabbedItem(jc, key)]))
		self.assertTrue(jc.has_item(NanoKey))
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [armor, pistol])

		events = dungeon.grab_item(jc, pistol)
		self.assertEqual(_R(events), _R([game.Event.GrabbedItem(jc, pistol)]))
		self.assertTrue(jc.has_item(StealthPistol))
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [armor])

		events = dungeon.grab_item(jc, armor)
		self.assertEqual(_R(events), _R([game.Event.InventoryFull(armor)]))
		self.assertFalse(jc.has_item(ThermopticCamo))
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [armor])
	def should_drop_item(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')

		pistol = StealthPistol()
		jc = UNATCOAgent(None)
		jc.inventory.append(pistol)
		jc.pos = Point(1, 1)

		gridmap = dungeon.scene
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [])
		events = dungeon.drop_item(jc, pistol)
		self.assertEqual(_R(events), _R([game.Event.MonsterDroppedItem(jc, pistol)]))
		self.assertFalse(jc.has_item(StealthPistol))
		self.assertEqual(list(dungeon.scene.iter_items_at(Point(1, 1))), [pistol])
	def should_visit_tunnel(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		tunnel = Scene.Tunnel(Point(2, 2), Point(6, 12), 'H', bending_point=2)
		dungeon.scene.tunnels.append(tunnel)
		dungeon.visited_tunnels['top'].append(set())
		dungeon.visit_tunnel(tunnel, Point(2, 2), adjacent=False)
		self.assertEqual(dungeon.visited_tunnels['top'][-1], {Point(2, 2)})
		dungeon.visit_tunnel(tunnel, Point(4, 2), adjacent=True)
		self.assertEqual(dungeon.visited_tunnels['top'][-1], {
			Point(2, 2),
			Point(3, 2), Point(4, 2), Point(4, 3),
			})
	def should_visit_places(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		gridmap = dungeon.scene

		dungeon.visit(Point(1, 1))
		self.assertTrue(dungeon.visited_rooms['top'].cell((0, 0)))
		self.assertEqual(dungeon.visited_tunnels['top'][0], {Point(3, 1)})

		dungeon.visit(Point(9, 2))
		self.assertTrue(dungeon.visited_rooms['top'].cell((1, 0)))
		self.assertEqual(dungeon.visited_tunnels['top'][0], {Point(3, 1), Point(7, 3)})

		dungeon.visit(Point(5, 1))
		self.assertEqual(dungeon.visited_tunnels['top'][0], {Point(3, 1),
			Point(4, 1), Point(5, 1),
			Point(5, 2),
			Point(7, 3),
			})

class TestDungeon(unittest.TestCase):
	class UNATCO(game.Dungeon):
		GENERATOR = MockGenerator
		PLAYER_TYPE = UNATCOAgent
	def should_iter_dungeon_cells(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		dungeon.scene.get_player().pos = Point(3, 1)
		dungeon.visit(dungeon.scene.get_player().pos)
		dungeon.scene.get_player().pos = Point(5, 1)
		dungeon.visit(dungeon.scene.get_player().pos)
		dungeon.scene.get_player().pos = Point(5, 3)
		dungeon.visit(dungeon.scene.get_player().pos)
		dungeon.scene.get_player().pos = Point(7, 3)
		dungeon.visit(dungeon.scene.get_player().pos)
		mj12 = MJ12Trooper(None)
		mj12.pos = Point(8, 3)
		dungeon.scene.monsters.append(mj12)
		pistol = StealthPistol()
		dungeon.scene.items.append((Point(9, 2), pistol))

		view = Matrix((80, 25), '_')
		for pos, (terrain, objects, items, monsters) in dungeon.scene.iter_cells(None):
			is_visible = dungeon.is_visible(pos) or dungeon.god.vision
			if monsters and is_visible:
				view.set_cell(pos, monsters[-1].sprite)
			elif items and (dungeon.is_remembered(pos) or is_visible):
				view.set_cell(pos, items[-1].sprite)
			elif objects and (dungeon.is_remembered(pos) or is_visible):
				view.set_cell(pos, objects[-1].sprite)
			else:
				terrain, remembered = terrain
				if is_visible:
					view.set_cell(pos, terrain)
				elif dungeon.is_remembered(pos):
					view.set_cell(pos, remembered)
		expected = textwrap.dedent("""\
				+--+____________________________________________________________________________
				|> +##_+----+___________________________________________________________________
				+--+_#_|.(..|___________________________________________________________________
				_____##@M...|___________________________________________________________________
				_______+---++___________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				________________________________________________________________________________
				""")
		self.maxDiff = None
		self.assertEqual(view.tostring(), expected)
	def should_move_to_level(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		self.assertEqual(dungeon.scene, dungeon.levels['top'])
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 1))
	def should_use_stairs(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		dungeon.use_stairs(dungeon.scene.get_player(), dungeon.scene.objects[1][1])
		self.assertEqual(dungeon.scene, dungeon.levels['roof'])
		self.assertEqual(dungeon.scene.get_player().pos, Point(1, 1))
	def should_locate_in_maze(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		self.assertEqual(dungeon.scene, dungeon.levels['top'])

		dungeon.scene.get_player().pos = Point(1, 1)
		self.assertEqual(dungeon.scene.current_room, dungeon.scene.rooms.cell((0, 0)))
		self.assertIsNone(dungeon.scene.current_tunnel)

		dungeon.scene.get_player().pos = Point(3, 1)
		self.assertEqual(dungeon.scene.current_room, dungeon.scene.rooms.cell((0, 0)))
		self.assertEqual(dungeon.scene.current_tunnel, dungeon.scene.tunnels[0])

		dungeon.scene.get_player().pos = Point(5, 1)
		self.assertIsNone(dungeon.scene.current_room)
		self.assertEqual(dungeon.scene.current_tunnel, dungeon.scene.tunnels[0])
	def should_detect_visible_objects(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		self.assertEqual(dungeon.scene, dungeon.levels['top'])

		dungeon.scene.get_player().pos = Point(1, 1)
		dungeon.visit(dungeon.scene.get_player().pos)
		self.assertTrue(dungeon.is_visible(dungeon.scene.rooms.cell((0, 0))))
		self.assertFalse(dungeon.is_visible(dungeon.scene.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_visible(dungeon.scene.tunnels[0], additional=Point(3, 1)))
		self.assertFalse(dungeon.is_visible(dungeon.scene.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_visible(Point(2, 1)))
		self.assertTrue(dungeon.is_visible(Point(3, 1)))
		self.assertFalse(dungeon.is_visible(Point(5, 1)))
		self.assertFalse(dungeon.is_visible(Point(8, 2)))

		dungeon.god.vision = True
		self.assertTrue(dungeon.is_visible(dungeon.scene.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_visible(dungeon.scene.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_visible(Point(5, 1)))
		self.assertTrue(dungeon.is_visible(Point(8, 2)))
	def should_remember_objects(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		self.assertEqual(dungeon.scene, dungeon.levels['top'])

		dungeon.scene.get_player().pos = Point(1, 1)
		dungeon.visit(dungeon.scene.get_player().pos)
		dungeon.scene.get_player().pos = Point(2, 6)

		self.assertTrue(dungeon.is_remembered(dungeon.scene.rooms.cell((0, 0))))
		self.assertFalse(dungeon.is_remembered(dungeon.scene.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_remembered(dungeon.scene.tunnels[0], additional=Point(3, 1)))
		self.assertFalse(dungeon.is_remembered(dungeon.scene.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_remembered(Point(2, 1)))
		self.assertTrue(dungeon.is_remembered(Point(3, 1)))
		self.assertFalse(dungeon.is_remembered(Point(5, 1)))
		self.assertFalse(dungeon.is_remembered(Point(8, 2)))

		dungeon.god.vision = True
		self.assertTrue(dungeon.is_remembered(dungeon.scene.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_remembered(dungeon.scene.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_remembered(Point(5, 1)))
		self.assertTrue(dungeon.is_remembered(Point(8, 2)))
	def should_move_monster(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level(dungeon.PLAYER_TYPE(None), 'top', connected_passage='basement')
		dungeon.scene.get_player().pos = Point(9, 3)
		pistol = StealthPistol()
		dungeon.scene.get_player().inventory.append(pistol)

		mj12 = MJ12Trooper(None)
		mj12.pos = Point(8, 3)
		dungeon.scene.monsters.append(mj12)

		vacuum = VacuumCleaner(None)
		vacuum.pos = Point(8, 2)
		dungeon.scene.monsters.append(vacuum)

		events = dungeon.move_monster(mj12, Point(7, 3))
		self.assertEqual(mj12.pos, Point(7, 3))
		self.assertEqual(events, [])

		events = dungeon.move_monster(mj12, Point(6, 3), with_tunnels=False)
		self.assertEqual(mj12.pos, Point(7, 3))
		self.assertEqual(_R(events), _R([game.Event.BumpIntoTerrain(mj12, Point(6, 3))]))

		events = dungeon.move_monster(mj12, Point(8, 3))
		self.assertEqual(mj12.pos, Point(8, 3))
		self.assertEqual(events, [])

		events = dungeon.move_monster(mj12, Point(8, 2))
		self.assertEqual(mj12.pos, Point(8, 3))
		self.assertEqual(_R(events), _R([game.Event.BumpIntoMonster(mj12, vacuum)]))

		events = dungeon.move_monster(mj12, Point(9, 3))
		self.assertEqual(mj12.pos, Point(8, 3))
		self.assertEqual(_R(events), _R([game.Event.AttackMonster(mj12, dungeon.scene.get_player(), 3)]))
		self.assertEqual(dungeon.scene.get_player().hp, 97)

		dungeon.scene.get_player().hp = 3
		player = dungeon.scene.get_player()
		events = dungeon.move_monster(mj12, Point(9, 3))
		self.assertEqual(mj12.pos, Point(8, 3))
		self.assertEqual(_R(events), _R([
			game.Event.AttackMonster(mj12, player, 3),
			game.Event.MonsterDied(player),
			game.Event.MonsterDroppedItem(player, pistol),
			]))
		self.assertTrue(dungeon.is_finished())
		self.assertEqual(dungeon.scene.items, [items.ItemAtPos(Point(9, 3), pistol)])
