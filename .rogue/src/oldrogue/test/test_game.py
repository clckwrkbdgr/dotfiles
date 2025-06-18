from clckwrkbdgr import unittest
import textwrap, functools
from clckwrkbdgr.math import Point, Matrix, get_neighbours
from .. import game
from ..game import Item, Wearable, Consumable, LevelPassage
from ..game import Monster
from ..game import Tunnel, Room, GridRoomMap, Dungeon
from ...engine import events

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

class ThermopticCamo(Item, Wearable):
	_protection = 3

class HazmatSuit(Item, Wearable):
	_protection = 1

class StimPack(Item, Consumable):
	def consume_by(self, monster):
		monster.heal(25)
		return []

class SmartStimPack(Item, Consumable):
	def consume_by(self, monster):
		if monster.hp >= monster.max_hp:
			return None
		else: # pragma: no cover
			raise RuntimeError("Should never reach here.")

class UNATCOAgent(Monster):
	_attack = 2
	_max_hp = 100
	_max_inventory = 2

class VacuumCleaner(Monster):
	_max_hp = 5

class NSFTerrorist(Monster):
	_attack = 1
	_max_hp = 50

class MJ12Trooper(Monster):
	_attack = 3
	_max_hp = 200
	_hostile_to = [UNATCOAgent, NSFTerrorist]

class TestUtils(unittest.TestCase):
	def should_detect_diagonal_movement(self):
		self.assertTrue(game.is_diagonal_movement(Point(0, 0), Point(1, 1)))
		self.assertTrue(game.is_diagonal_movement(Point(0, 0), Point(1, -1)))
		self.assertFalse(game.is_diagonal_movement(Point(0, 0), Point(1, 0)))
		self.assertFalse(game.is_diagonal_movement(Point(0, 0), Point(0, 1)))

class TestMonster(unittest.TestCase):
	def should_heal(self):
		jc = UNATCOAgent()
		jc.hp = 50
		jc.heal(70)
		self.assertEqual(jc.hp, 100)
	def should_detect_hostiles(self):
		jc = UNATCOAgent()
		nsf = NSFTerrorist()
		mj12 = MJ12Trooper()
		self.assertTrue(mj12.is_hostile_to(nsf))
		self.assertTrue(mj12.is_hostile_to(jc))
		self.assertFalse(jc.is_hostile_to(nsf))
	def should_detect_items_in_inventory(self):
		key = NanoKey()
		key.value = '0451'
		jc = UNATCOAgent()
		jc.inventory.append(key)
		self.assertTrue(jc.has_item(NanoKey, value='0451'))
		self.assertFalse(jc.has_item(NanoKey, value='666'))
		self.assertTrue(jc.has_item(NanoKey))
		self.assertFalse(jc.has_item(StealthPistol))
	def should_equip_items(self):
		key = NanoKey()
		key.value = '0451'
		pistol = StealthPistol()
		armor = ThermopticCamo()
		hazmat = HazmatSuit()

		jc = UNATCOAgent()
		jc.inventory.append(key)
		jc.inventory.append(pistol)
		jc.inventory.append(armor)

		self.assertEqual(_R(jc.wield(pistol)), _R([
			game.Event.Wielding(jc, pistol),
			]))
		self.assertEqual(_R(jc.wield(key)), _R([
			game.Event.Unwielding(jc, pistol),
			game.Event.Wielding(jc, key),
			]))
		self.assertEqual(_R(jc.wear(armor)), _R([
			game.Event.Wearing(jc, armor),
			]))
		self.assertEqual(_R(jc.wear(hazmat)), _R([
			game.Event.TakingOff(jc, armor),
			game.Event.Wearing(jc, hazmat),
			]))
		self.assertEqual(_R(jc.wield(hazmat)), _R([
			game.Event.TakingOff(jc, hazmat),
			game.Event.Unwielding(jc, key),
			game.Event.Wielding(jc, hazmat),
			]))
		self.assertEqual(_R(jc.wear(pistol)), _R([
			game.Event.NotWearable(pistol),
			]))
		self.assertEqual(_R(jc.wear(armor)), _R([
			game.Event.Wearing(jc, armor),
			]))
		self.assertEqual(_R(jc.wear(hazmat)), _R([
			game.Event.Unwielding(jc, hazmat),
			game.Event.TakingOff(jc, armor),
			game.Event.Wearing(jc, hazmat),
			]))
		jc.wield(pistol)
		self.assertEqual(_R(jc.wield(None)), _R([
			game.Event.Unwielding(jc, pistol),
			]))
		self.assertEqual(_R(jc.wear(None)), _R([
			game.Event.TakingOff(jc, hazmat),
			]))
	def should_drop_items(self):
		key = NanoKey()
		key.value = '0451'
		pistol = StealthPistol()
		armor = ThermopticCamo()
		hazmat = HazmatSuit()

		jc = UNATCOAgent()
		jc.inventory.append(key)
		jc.inventory.append(pistol)
		jc.inventory.append(armor)

		jc.wear(armor)
		jc.wield(pistol)

		self.assertEqual(_R(jc.drop(key)), _R([
			game.Event.MonsterDroppedItem(jc, key),
			]))
		self.assertFalse(jc.has_item(NanoKey))
		self.assertEqual(_R(jc.drop(pistol)), _R([
			game.Event.Unwielding(jc, pistol),
			game.Event.MonsterDroppedItem(jc, pistol),
			]))
		self.assertFalse(jc.has_item(StealthPistol))
		self.assertEqual(_R(jc.drop(armor)), _R([
			game.Event.TakingOff(jc, armor),
			game.Event.MonsterDroppedItem(jc, armor),
			]))
		self.assertFalse(jc.has_item(ThermopticCamo))
	def should_consumeItems(self):
		key = NanoKey()
		key.value = '0451'
		stimpack = StimPack()
		smart_stimpack = SmartStimPack()

		jc = UNATCOAgent()
		jc.inventory.append(key)
		jc.inventory.append(stimpack)
		jc.inventory.append(smart_stimpack)

		self.assertEqual(_R(jc.consume(key)), _R([
			game.Event.NotConsumable(key),
			]))
		self.assertTrue(jc.has_item(NanoKey))

		jc.wield(stimpack)
		self.assertEqual(_R(jc.consume(stimpack)), _R([
			game.Event.Unwielding(jc, stimpack),
			game.Event.MonsterConsumedItem(jc, stimpack),
			]))
		self.assertFalse(jc.has_item(StimPack))
		self.assertEqual(jc.hp, jc.max_hp)

		jc.wield(smart_stimpack)
		self.assertEqual(_R(jc.consume(smart_stimpack)), _R([
			game.Event.Unwielding(jc, smart_stimpack),
			]))
		self.assertTrue(jc.has_item(SmartStimPack))
	def should_calc_attack_damage(self):
		pistol = StealthPistol()
		armor = ThermopticCamo()

		jc = UNATCOAgent()
		jc.inventory.append(pistol)
		jc.inventory.append(armor)

		self.assertEqual(jc.get_attack_damage(), 2)
		jc.wield(armor)
		self.assertEqual(jc.get_attack_damage(), 2)
		jc.wield(pistol)
		self.assertEqual(jc.get_attack_damage(), 7)

		vacuum = VacuumCleaner()
		self.assertEqual(vacuum.get_attack_damage(), 0)
	def should_calc_protection(self):
		pistol = StealthPistol()
		armor = ThermopticCamo()

		jc = UNATCOAgent()
		jc.inventory.append(pistol)
		jc.inventory.append(armor)

		self.assertEqual(jc.get_protection(), 0)
		jc.wear(armor)
		self.assertEqual(jc.get_protection(), 3)
	def should_attack_other_monster(self):
		pistol = StealthPistol()
		armor = ThermopticCamo()

		jc = UNATCOAgent()
		jc.inventory.append(pistol)

		mj12 = MJ12Trooper()
		mj12.inventory.append(armor)

		self.assertEqual(jc.attack(mj12), 2)
		self.assertEqual(mj12.hp, 198)

		jc.wield(pistol)
		self.assertEqual(jc.attack(mj12), 7)
		self.assertEqual(mj12.hp, 191)

		mj12.wear(armor)
		self.assertEqual(jc.attack(mj12), 4)
		self.assertEqual(mj12.hp, 187)

class TestTerrain(unittest.TestCase):
	def should_visit_tunnel(self):
		tunnel = game.Tunnel(Point(2, 2), Point(6, 12), 'H', bending_point=2)
		tunnel.visit(Point(2, 2), adjacent=False)
		self.assertEqual(tunnel.visited, {Point(2, 2)})
		tunnel.visit(Point(4, 2), adjacent=True)
		self.assertEqual(tunnel.visited, {
			Point(2, 2),
			Point(3, 2), Point(4, 2), Point(4, 3),
			})

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
		result = GridRoomMap()
		if level_id == 'top':
			result.rooms, result.tunnels[:], result.objects[:] = MockGenerator._parse_layout(self.MAIN_LEVEL)
		elif level_id == 'roof':
			result.rooms, result.tunnels[:], result.objects[:] = MockGenerator._parse_layout(self.ROOF)
		return result
	@staticmethod
	@functools.lru_cache()
	def _parse_layout(layout):
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
			rooms.set_cell((0, 0), Room(*(rects[0])))
			rooms.set_cell((1, 0), Room(*(rects[1])))
			rooms.set_cell((0, 1), Room(*(rects[2])))
			rooms.set_cell((1, 1), Room(*(rects[3])))
		else:
			rooms = Matrix((1, 1))
			rooms.set_cell((0, 0), Room(*(rects[0])))

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
				tunnels.append(Tunnel(path[0], path[-1], direction, bending or 1))

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
		mj12 = MJ12Trooper()
		pistol = StealthPistol()
		armor = ThermopticCamo()

		gridmap = self._map()
		gridmap.items.append( (Point(1, 1), pistol) )
		gridmap.items.append( (Point(1, 1), armor) )
		mj12.pos = Point(9, 2)
		gridmap.monsters.append(mj12)

		elevator = gridmap.objects[0][1]

		self.assertEqual(list(gridmap.items_at(Point(2, 1))), [])
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [armor, pistol])
		self.assertEqual(list(gridmap.objects_at(Point(1, 2))), [])
		self.assertEqual(list(gridmap.objects_at(Point(1, 1))), [elevator])
		self.assertEqual(list(gridmap.monsters_at(Point(9, 2))), [mj12])
	def should_rip_monster(self):
		pistol = StealthPistol()
		armor = ThermopticCamo()

		mj12 = MJ12Trooper()
		mj12.inventory.append(pistol)
		mj12.inventory.append(armor)

		gridmap = self._map()
		mj12.pos = Point(9, 2)
		gridmap.monsters.append(mj12)
		self.assertTrue(mj12.is_alive())
		with self.assertRaises(RuntimeError):
			list(gridmap.rip(mj12))
		self.assertTrue(mj12.is_alive())
		self.assertEqual(list(gridmap.monsters_at(Point(9, 2))), [mj12])

		mj12.hp = 0
		loot = list(gridmap.rip(mj12))
		self.assertEqual(loot, [armor, pistol])
		self.assertEqual(list(gridmap.monsters_at(Point(9, 2))), [])
	def should_grab_item(self):
		pistol = StealthPistol()
		armor = ThermopticCamo()

		jc = UNATCOAgent()

		gridmap = self._map()
		key = NanoKey()
		gridmap.items.append( (Point(1, 1), key) )
		gridmap.items.append( (Point(1, 1), pistol) )
		gridmap.items.append( (Point(1, 1), armor) )
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [armor, pistol, key])

		events = gridmap.grab_item(jc, key)
		self.assertEqual(_R(events), _R([game.Event.GrabbedItem(jc, key)]))
		self.assertTrue(jc.has_item(NanoKey))
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [armor, pistol])

		events = gridmap.grab_item(jc, pistol)
		self.assertEqual(_R(events), _R([game.Event.GrabbedItem(jc, pistol)]))
		self.assertTrue(jc.has_item(StealthPistol))
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [armor])

		events = gridmap.grab_item(jc, armor)
		self.assertEqual(_R(events), _R([game.Event.InventoryFull(armor)]))
		self.assertFalse(jc.has_item(ThermopticCamo))
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [armor])
	def should_drop_item(self):
		pistol = StealthPistol()
		jc = UNATCOAgent()
		jc.inventory.append(pistol)
		jc.pos = Point(1, 1)

		gridmap = self._map()
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [])
		events = gridmap.drop_item(jc, pistol)
		self.assertEqual(_R(events), _R([game.Event.MonsterDroppedItem(jc, pistol)]))
		self.assertFalse(jc.has_item(StealthPistol))
		self.assertEqual(list(gridmap.items_at(Point(1, 1))), [pistol])
	def should_visit_places(self):
		gridmap = self._map()

		gridmap.visit(Point(1, 1))
		self.assertTrue(gridmap.rooms.cell((0, 0)).visited)
		self.assertEqual(gridmap.tunnels[0].visited, {Point(3, 1)})

		gridmap.visit(Point(9, 2))
		self.assertTrue(gridmap.rooms.cell((1, 0)).visited)
		self.assertEqual(gridmap.tunnels[0].visited, {Point(3, 1), Point(7, 3)})

		gridmap.visit(Point(5, 1))
		self.assertEqual(gridmap.tunnels[0].visited, {Point(3, 1),
			Point(4, 1), Point(5, 1),
			Point(5, 2),
			Point(7, 3),
			})

class TestDungeon(unittest.TestCase):
	class UNATCO(game.Dungeon):
		GENERATOR = MockGenerator
		PLAYER_TYPE = UNATCOAgent
	def should_move_to_level(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level('top', connected_passage='basement')
		self.assertEqual(dungeon.current_level, dungeon.levels['top'])
		self.assertEqual(dungeon.rogue.pos, Point(1, 1))
	def should_use_stairs(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level('top', connected_passage='basement')
		dungeon.use_stairs(dungeon.current_level.objects[1][1])
		self.assertEqual(dungeon.current_level, dungeon.levels['roof'])
		self.assertEqual(dungeon.rogue.pos, Point(1, 1))
	def should_locate_in_maze(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level('top', connected_passage='basement')
		self.assertEqual(dungeon.current_level, dungeon.levels['top'])

		dungeon.rogue.pos = Point(1, 1)
		self.assertEqual(dungeon.current_room, dungeon.current_level.rooms.cell((0, 0)))
		self.assertIsNone(dungeon.current_tunnel)

		dungeon.rogue.pos = Point(3, 1)
		self.assertEqual(dungeon.current_room, dungeon.current_level.rooms.cell((0, 0)))
		self.assertEqual(dungeon.current_tunnel, dungeon.current_level.tunnels[0])

		dungeon.rogue.pos = Point(5, 1)
		self.assertIsNone(dungeon.current_room)
		self.assertEqual(dungeon.current_tunnel, dungeon.current_level.tunnels[0])
	def should_detect_visible_objects(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level('top', connected_passage='basement')
		self.assertEqual(dungeon.current_level, dungeon.levels['top'])

		dungeon.rogue.pos = Point(1, 1)
		dungeon.current_level.visit(dungeon.rogue.pos)
		self.assertTrue(dungeon.is_visible(dungeon.current_level.rooms.cell((0, 0))))
		self.assertFalse(dungeon.is_visible(dungeon.current_level.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_visible(dungeon.current_level.tunnels[0], additional=Point(3, 1)))
		self.assertFalse(dungeon.is_visible(dungeon.current_level.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_visible(Point(2, 1)))
		self.assertTrue(dungeon.is_visible(Point(3, 1)))
		self.assertFalse(dungeon.is_visible(Point(5, 1)))
		self.assertFalse(dungeon.is_visible(Point(8, 2)))

		dungeon.god.vision = True
		self.assertTrue(dungeon.is_visible(dungeon.current_level.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_visible(dungeon.current_level.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_visible(Point(5, 1)))
		self.assertTrue(dungeon.is_visible(Point(8, 2)))
	def should_remember_objects(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level('top', connected_passage='basement')
		self.assertEqual(dungeon.current_level, dungeon.levels['top'])

		dungeon.rogue.pos = Point(1, 1)
		dungeon.current_level.visit(dungeon.rogue.pos)
		dungeon.rogue.pos = Point(2, 6)

		self.assertTrue(dungeon.is_remembered(dungeon.current_level.rooms.cell((0, 0))))
		self.assertFalse(dungeon.is_remembered(dungeon.current_level.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_remembered(dungeon.current_level.tunnels[0], additional=Point(3, 1)))
		self.assertFalse(dungeon.is_remembered(dungeon.current_level.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_remembered(Point(2, 1)))
		self.assertTrue(dungeon.is_remembered(Point(3, 1)))
		self.assertFalse(dungeon.is_remembered(Point(5, 1)))
		self.assertFalse(dungeon.is_remembered(Point(8, 2)))

		dungeon.god.vision = True
		self.assertTrue(dungeon.is_remembered(dungeon.current_level.rooms.cell((1, 0))))
		self.assertTrue(dungeon.is_remembered(dungeon.current_level.tunnels[1], additional=Point(11, 4)))
		self.assertTrue(dungeon.is_remembered(Point(5, 1)))
		self.assertTrue(dungeon.is_remembered(Point(8, 2)))
	def should_move_monster(self):
		dungeon = self.UNATCO()
		dungeon.go_to_level('top', connected_passage='basement')
		dungeon.rogue.pos = Point(9, 3)
		pistol = StealthPistol()
		dungeon.rogue.inventory.append(pistol)

		mj12 = MJ12Trooper()
		mj12.pos = Point(8, 3)
		dungeon.current_level.monsters.append(mj12)

		vacuum = VacuumCleaner()
		vacuum.pos = Point(8, 2)
		dungeon.current_level.monsters.append(vacuum)

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
		self.assertEqual(_R(events), _R([game.Event.AttackMonster(mj12, dungeon.rogue, 3)]))
		self.assertEqual(dungeon.rogue.hp, 97)

		dungeon.rogue.hp = 3
		events = dungeon.move_monster(mj12, Point(9, 3))
		self.assertEqual(mj12.pos, Point(8, 3))
		self.assertEqual(_R(events), _R([
			game.Event.AttackMonster(mj12, dungeon.rogue, 3),
			game.Event.MonsterDied(dungeon.rogue),
			game.Event.MonsterDroppedItem(dungeon.rogue, pistol),
			]))
		self.assertTrue(dungeon.is_finished())
		self.assertEqual(dungeon.current_level.items, [(Point(9, 3), pistol)])
