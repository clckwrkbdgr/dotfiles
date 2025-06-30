from clckwrkbdgr.math import Point
from .. import pcg as builders
from .. import pcg as settlers
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
			'healing_potion' : items.ItemType('healing potion', '!', items.Effect.HEALING),
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

class MockMapping:
	_ = {_key:terrain.Cell(_item) for (_key, _item) in MockGame.TERRAIN.items()}
	@staticmethod
	def start(): return 'start'
	@staticmethod
	def exit(): return 'exit'
	@staticmethod
	def monster(pos,*data):
		return monsters.Monster(monsters.Species('monster', "M", 3, vision=10), *(data + (pos,)))
	@staticmethod
	def thief(pos,*data):
		return monsters.Monster(monsters.Species('thief', "T", 3, vision=10, drops=[
		(1, 'money'),
		]), *(data + (pos,)))
	@staticmethod
	def potion(*data):
		return items.Item(items.ItemType('potion', '!', items.Effect.NONE), *data)
	@staticmethod
	def healing_potion(*data):
		return items.Item(items.ItemType('healing potion', '!', items.Effect.HEALING), *data)

class _MockBuilderSingleMockThief(settlers.CustomMapSingleMonster):
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
	PASSABLE = ('.',)
	MONSTER = ('thief', monsters.Behavior.ANGRY)

class _MockBuilderSingleMockMonster(settlers.CustomMapSingleMonster):
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
	PASSABLE = ('.',)
	MONSTER = ('monster', monsters.Behavior.ANGRY)

class _MockBuilder_PotionsLyingAround(settlers.CustomSettler):
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
	ITEMS = [
		(Point(10, 6), 'potion'),
		(Point(11, 6), 'healing_potion'),
		]

class _MockBuilder_MockSettler(settlers.CustomSettler):
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
	MONSTERS = [
			(Point(2, 5), 'monster', monsters.Behavior.DUMMY),
			]
	ITEMS = [
			(Point(10, 6), 'potion'),
			]

class _MockBuilderUnSettler(settlers.CustomSettler):
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

class _MockBuilder_NowYouSeeMe(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(1, 1), 'monster', monsters.Behavior.DUMMY),
		(Point(1, 6), 'monster', monsters.Behavior.DUMMY),
		]

class _MockMiniRogueBuilderUnSettler(settlers.CustomSettler):
	Mapping = MockMapping
	MAP_DATA = """\
		  +--+ % 
		* |@.| % 
		**^..^%% 
		  |.>|   
		  +--+   
		"""

class _MockMiniBuilderUnSettler(settlers.CustomSettler):
	Mapping = MockMapping
	MAP_DATA = """\
		@#..#
		~#..#
		~~.>#
		#####
		"""

class _MockBuilder_MonstersOnTopOfItems(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(1, 1), 'monster', monsters.Behavior.DUMMY),
		(Point(1, 6), 'monster', monsters.Behavior.DUMMY),
		]
	ITEMS = [
		(Point(2, 6), 'potion'),
		(Point(1, 6), 'potion'),
		]

class _MockBuilder_CloseMonster(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(10, 6), 'monster', monsters.Behavior.DUMMY),
		]

class _MockBuilder_CloseThief(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(10, 6), 'thief', monsters.Behavior.DUMMY),
		]

class _MockBuilder_CloseInertMonster(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(10, 6), 'monster', monsters.Behavior.INERT),
		]

class _MockBuilder_CloseAngryMonster(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(11, 6), 'monster', monsters.Behavior.ANGRY),
		]

class _MockBuilder_CloseAngryMonster2(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(4, 4), 'monster', monsters.Behavior.ANGRY),
		]

class _MockBuilder_FightingGround(settlers.CustomSettler):
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
	MONSTERS = [
		(Point(10, 6), 'monster', monsters.Behavior.DUMMY),
		(Point(9, 4), 'monster', monsters.Behavior.INERT),
		]

def build(dungeon_id):
	_DATA = {
			'now you see me': ([_MockBuilder_NowYouSeeMe]),
			'mini dark rogue': ([_MockMiniRogueBuilderUnSettler]),
			'lonely': ([_MockBuilderUnSettler]),
			'monsters on top': ([_MockBuilder_MonstersOnTopOfItems]),
			'mini lonely': ([_MockMiniBuilderUnSettler]),
			'mini 2 lonely': ([_MockMiniBuilderUnSettler]),
			'mini 3 lonely': ([_MockMiniBuilderUnSettler]),
			'mini 4 lonely': ([_MockMiniBuilderUnSettler]),
			'mini 5 lonely': ([_MockMiniBuilderUnSettler]),
			'mini 6 monster': ([_MockBuilder_NowYouSeeMe]),
			'mini 6 lonely': ([_MockMiniBuilderUnSettler]),
			'mini rogue 2 lonely': ([_MockMiniRogueBuilderUnSettler]),
			'mini rogue lonely': ([_MockMiniRogueBuilderUnSettler]),
			'potions lying around': ([_MockBuilder_PotionsLyingAround]),
			'close monster': ([_MockBuilder_CloseMonster]),
			'close thief': ([_MockBuilder_CloseThief]),
			'close inert monster': ([_MockBuilder_CloseInertMonster]),
			'close angry monster': ([_MockBuilder_CloseAngryMonster]),
			'close angry monster 2': ([_MockBuilder_CloseAngryMonster2]),
			'single mock monster': ([_MockBuilderSingleMockMonster]),
			'single mock thief': ([_MockBuilderSingleMockThief]),
			'mock settler': ([_MockBuilder_MockSettler]),
			'mock settler restored': ([_MockBuilder_MockSettler]),
			'fighting around': ([_MockBuilder_FightingGround]),
			'potions lying around 2': ([_MockBuilder_PotionsLyingAround]),
			'monster and potion': ([_MockBuilder_MockSettler]),
			}
	game = MockGame(rng_seed=0, builders=_DATA[dungeon_id])
	game.generate()
	return game
