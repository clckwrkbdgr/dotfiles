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
		'#' : terrain.Terrain('#', "#", False, remembered='#'),
		'.' : terrain.Terrain('.', ".", True),
		'~' : terrain.Terrain('~', ".", True, allow_diagonal=False),
		}

class MockRogueDungeon(MockGame):
	TERRAIN = {
		None : terrain.Terrain(' ', ' ', False),
		' ' : terrain.Terrain(' ', ' ', False),
		'#' : terrain.Terrain('#', "#", True, remembered='#', allow_diagonal=False, dark=True),
		'%' : terrain.Terrain('#', "#", True, allow_diagonal=False, dark=True),
		'.' : terrain.Terrain('.', ".", True),
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
		+--+ #
		|@.| #
		|..^##
		|.>|  
		+--+  
		"""

class _MockMiniRogue2Builder(builders.CustomMap):
	MAP_DATA = """\
		+--+  
		|.@| #
		|..^##
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

def build(dungeon_id):
	import sys
	self = sys.modules[__name__]
	if dungeon_id == 'now you see me':
		return MockGame(rng_seed=0, builders=[_MockBuilder], settlers=[_NowYouSeeMe])
	if dungeon_id == 'mini dark rogue':
		return MockRogueDungeon(rng_seed=0, builders=[_MockMiniDarkRogueBuilder], settlers=[UnSettler])
	if dungeon_id == 'lonely':
		return MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[UnSettler])
	if dungeon_id == 'monsters on top':
		return MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_MonstersOnTopOfItems])
	if dungeon_id == 'mini lonely':
		return MockGame(rng_seed=0, builders=[_MockMiniBuilder], settlers=[UnSettler])
	if dungeon_id == 'mini 2 lonely':
		return MockGame(rng_seed=0, builders=[_MockMini2Builder], settlers=[UnSettler])
	if dungeon_id == 'mini 3 lonely':
		dungeon = MockGame(rng_seed=0, builders=[_MockMini3Builder], settlers=[UnSettler])
	if dungeon_id == 'mini 4 lonely':
		dungeon = MockGame(rng_seed=0, builders=[_MockMini4Builder], settlers=[UnSettler])
	if dungeon_id == 'mini 5 lonely':
		dungeon = MockGame(rng_seed=0, builders=[_MockMini5Builder], settlers=[UnSettler])
	if dungeon_id == 'mini 6 monster':
		dungeon = MockGame(rng_seed=0, builders=[_MockMini6Builder], settlers=[SingleMockMonster])
	if dungeon_id == 'mini 6 lonely':
		dungeon = MockGame(rng_seed=0, builders=[_MockMini6Builder], settlers=[UnSettler])
	if dungeon_id == 'mini rogue 2 lonely':
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockMiniRogue2Builder], settlers=[UnSettler])
	if dungeon_id == 'mini rogue lonely':
		dungeon = MockRogueDungeon(rng_seed=0, builders=[_MockMiniRogueBuilder], settlers=[UnSettler])
	if dungeon_id == 'potions lying around':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._PotionsLyingAround])
	if dungeon_id == 'close monster':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseMonster])
	if dungeon_id == 'close thief':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseThief])
	if dungeon_id == 'close inert monster':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseInertMonster])
	if dungeon_id == 'close angry monster':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseAngryMonster])
	if dungeon_id == 'close angry monster 2':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_CloseAngryMonster2])
	if dungeon_id == 'single mock monster':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[SingleMockMonster])
	if dungeon_id == 'single mock thief':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[SingleMockThief])
	if dungeon_id == 'mock settler':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler])
	if dungeon_id == 'mock settler restored':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MockSettler], load_from_reader=None)
	if dungeon_id == 'fighting around':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_FightingGround])
	if dungeon_id == 'potions lying around 2':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[_PotionsLyingAround2])
	if dungeon_id == 'monster and potion':
		dungeon = MockGame(rng_seed=0, builders=[self._MockBuilder], settlers=[self._MonsterAndPotion])
	return dungeon
