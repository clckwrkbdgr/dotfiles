from ..math import Point
from ..pcg import settlers, builders
from .. import terrain, items, monsters
from .. import game

class MockGame(game.Game):
	SPECIES = {
			'name' : monsters.Species('name', 'M', 100, vision=10, drops=[
				(1, 'money'),
				(2, 'potion'),
				]),
			'player' : monsters.Species('player', "@", 10, vision=10),
			'monster' : monsters.Species('monster', "M", 3, vision=10),
			'thief' : monsters.Species('thief', "T", 3, vision=10, drops=[
				(1, 'money'),
				]),
			}
	ITEMS = {
			'name' : items.ItemType('name', '!', items.Effect.NONE),
			'potion' : items.ItemType('potion', '!', items.Effect.NONE),
			'healing potion' : items.ItemType('healing potion', '!', items.Effect.HEALING),
			'money' : items.ItemType('money', '$', items.Effect.NONE),
			'weapon' : items.ItemType('weapon', '(', items.Effect.NONE),
			'ranged' : items.ItemType('ranged', ')', items.Effect.NONE),
			'rags' : items.ItemType('rags', '[', items.Effect.NONE),
			}
	TERRAIN = {
		None : terrain.Terrain(' ', ' ', False),
		'name' : terrain.Terrain('name', '.'),
		' ' : terrain.Terrain(' ', ' ', False),
		'#' : terrain.Terrain('#', "#", False, remembered='#'),
		'.' : terrain.Terrain('.', ".", True),
		'~' : terrain.Terrain('~', ".", True, allow_diagonal=False),
		# Rogue dungeon:
		'*' : terrain.Terrain('#', "#", True, remembered='#', allow_diagonal=False, dark=True),
		'%' : terrain.Terrain('#', "#", True, allow_diagonal=False, dark=True),
		'+' : terrain.Terrain('+', "+", False, remembered='+'),
		'-' : terrain.Terrain('-', "-", False, remembered='-'),
		'|' : terrain.Terrain('|', "|", False, remembered='|'),
		'^' : terrain.Terrain('^', "^", True, remembered='^', allow_diagonal=False, dark=True),
		}

class UnSettler(settlers.Settler):
	def _populate(self):
		pass

class CustomSettler(settlers.Settler):
	MONSTERS = [
			]
	ITEMS = [
			]
	def _populate(self):
		self.monsters += self.MONSTERS
	def _place_items(self):
		self.items += self.ITEMS

class SingleMockMonster(settlers.SingleMonster):
	MONSTER = ('monster', monsters.Behavior.ANGRY)

class SingleMockThief(settlers.SingleMonster):
	MONSTER = ('thief', monsters.Behavior.ANGRY)

class _PotionsLyingAround(CustomSettler):
	ITEMS = [
		('potion', Point(10, 6)),
		('healing potion', Point(11, 6)),
		]

class _PotionsLyingAround2(CustomSettler):
	ITEMS = [
		('potion', Point(10, 6)),
		]

class _MockSettler(CustomSettler):
	MONSTERS = [
			('monster', settlers.Behavior.ANGRY, Point(2, 5)),
			]
	ITEMS = [
			('potion', Point(10, 6)),
			]

class _NowYouSeeMe(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.DUMMY, Point(1, 1)),
		('monster', settlers.Behavior.DUMMY, Point(1, 6)),
		]

class _MockBuilder(builders.CustomMap):
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

class _MonsterAndPotion(settlers.Settler):
	MONSTERS = [
			('monster', settlers.Behavior.INERT, Point(2, 5)),
			]
	ITEMS = [
			('potion', Point(10, 6)),
			]
	def _populate(self):
		self.monsters += self.MONSTERS
	def _place_items(self):
		self.items += self.ITEMS

class _MockMiniDarkRogueBuilder(builders.CustomMap):
	MAP_DATA = """\
		+--+ %
		|@.| %
		|..^%%
		|.>|  
		+--+  
		"""

class _MockMiniRogueBuilder(builders.CustomMap):
	MAP_DATA = """\
		+--+ *
		|@.| *
		|..^**
		|.>|  
		+--+  
		"""

class _MockMiniRogue2Builder(builders.CustomMap):
	MAP_DATA = """\
		+--+  
		|.@| *
		|..^**
		|.>|  
		+--+  
		"""

class _MockMiniBuilder(builders.CustomMap):
	MAP_DATA = """\
		@...#
		....#
		...>#
		#####
		"""

class _MockMini2Builder(builders.CustomMap):
	MAP_DATA = """\
		#####
		#.@.#
		#..>#
		#####
		"""

class _MockMini3Builder(builders.CustomMap):
	MAP_DATA = """\
		######
		#.@#.#
		#...>#
		######
		"""

class _MockMini4Builder(builders.CustomMap):
	MAP_DATA = """\
		######
		#@#~>#
		#~#~##
		#~~~~#
		######
		"""

class _MockMini5Builder(builders.CustomMap):
	MAP_DATA = """\
		######
		#.@>.#
		#....#
		######
		"""

class _MockMini6Builder(builders.CustomMap):
	MAP_DATA = """\
		######
		#.@..#
		#...>#
		######
		"""

class _MonstersOnTopOfItems(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.DUMMY, Point(1, 1)),
		('monster', settlers.Behavior.DUMMY, Point(1, 6)),
		]
	ITEMS = [
		('potion', Point(2, 6)),
		('potion', Point(1, 6)),
		]

class _CloseMonster(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.DUMMY, Point(10, 6)),
		]

class _CloseThief(CustomSettler):
	MONSTERS = [
		('thief', settlers.Behavior.DUMMY, Point(10, 6)),
		]

class _CloseInertMonster(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.INERT, Point(10, 6)),
		]

class _CloseAngryMonster(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.ANGRY, Point(11, 6)),
		]

class _CloseAngryMonster2(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.ANGRY, Point(4, 4)),
		]

class _FightingGround(CustomSettler):
	MONSTERS = [
		('monster', settlers.Behavior.DUMMY, Point(10, 6)),
		('monster', settlers.Behavior.INERT, Point(9, 4)),
		]

def build(dungeon_id, load_from_reader=None):
	_DATA = {
			'now you see me': ([_MockBuilder], [_NowYouSeeMe]),
			'mini dark rogue': ([_MockMiniDarkRogueBuilder], [UnSettler]),
			'lonely': ([_MockBuilder], [UnSettler]),
			'monsters on top': ([_MockBuilder], [_MonstersOnTopOfItems]),
			'mini lonely': ([_MockMiniBuilder], [UnSettler]),
			'mini 2 lonely': ([_MockMini2Builder], [UnSettler]),
			'mini 3 lonely': ([_MockMini3Builder], [UnSettler]),
			'mini 4 lonely': ([_MockMini4Builder], [UnSettler]),
			'mini 5 lonely': ([_MockMini5Builder], [UnSettler]),
			'mini 6 monster': ([_MockMini6Builder], [SingleMockMonster]),
			'mini 6 lonely': ([_MockMini6Builder], [UnSettler]),
			'mini rogue 2 lonely': ([_MockMiniRogue2Builder], [UnSettler]),
			'mini rogue lonely': ([_MockMiniRogueBuilder], [UnSettler]),
			'potions lying around': ([_MockBuilder], [_PotionsLyingAround]),
			'close monster': ([_MockBuilder], [_CloseMonster]),
			'close thief': ([_MockBuilder], [_CloseThief]),
			'close inert monster': ([_MockBuilder], [_CloseInertMonster]),
			'close angry monster': ([_MockBuilder], [_CloseAngryMonster]),
			'close angry monster 2': ([_MockBuilder], [_CloseAngryMonster2]),
			'single mock monster': ([_MockBuilder], [SingleMockMonster]),
			'single mock thief': ([_MockBuilder], [SingleMockThief]),
			'mock settler': ([_MockBuilder], [_MockSettler]),
			'mock settler restored': ([_MockBuilder], [_MockSettler]),
			'fighting around': ([_MockBuilder], [_FightingGround]),
			'potions lying around 2': ([_MockBuilder], [_PotionsLyingAround2]),
			'monster and potion': ([_MockBuilder], [_MonsterAndPotion]),
			}
	return MockGame(rng_seed=0, builders=_DATA[dungeon_id][0], settlers=_DATA[dungeon_id][1], load_from_reader=load_from_reader)
