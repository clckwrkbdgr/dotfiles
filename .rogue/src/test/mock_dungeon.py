from clckwrkbdgr.math import Point
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

class _MockBuilderSingleMockThief(settlers.CustomMapSingleMonster):
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
	MONSTER = ('thief', monsters.Behavior.ANGRY)

class _MockBuilderSingleMockMonster(settlers.CustomMapSingleMonster):
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
	MONSTER = ('monster', monsters.Behavior.ANGRY)

class _MockBuilder_PotionsLyingAround(settlers.CustomSettler):
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
		('potion', Point(10, 6)),
		('healing potion', Point(11, 6)),
		]

class _MockBuilder_MockSettler(settlers.CustomSettler):
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
			('monster', settlers.Behavior.DUMMY, Point(2, 5)),
			]
	ITEMS = [
			('potion', Point(10, 6)),
			]

class _MockBuilderUnSettler(settlers.CustomSettler):
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
		('monster', settlers.Behavior.DUMMY, Point(1, 1)),
		('monster', settlers.Behavior.DUMMY, Point(1, 6)),
		]

class _MockMiniRogueBuilderUnSettler(settlers.CustomSettler):
	MAP_DATA = """\
		  +--+ % 
		* |@.| % 
		**^..^%% 
		  |.>|   
		  +--+   
		"""

class _MockMiniBuilderUnSettler(settlers.CustomSettler):
	MAP_DATA = """\
		@#..#
		~#..#
		~~.>#
		#####
		"""

class _MockBuilder_MonstersOnTopOfItems(settlers.CustomSettler):
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
		('monster', settlers.Behavior.DUMMY, Point(1, 1)),
		('monster', settlers.Behavior.DUMMY, Point(1, 6)),
		]
	ITEMS = [
		('potion', Point(2, 6)),
		('potion', Point(1, 6)),
		]

class _MockBuilder_CloseMonster(settlers.CustomSettler):
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
		('monster', settlers.Behavior.DUMMY, Point(10, 6)),
		]

class _MockBuilder_CloseThief(settlers.CustomSettler):
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
		('thief', settlers.Behavior.DUMMY, Point(10, 6)),
		]

class _MockBuilder_CloseInertMonster(settlers.CustomSettler):
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
		('monster', settlers.Behavior.INERT, Point(10, 6)),
		]

class _MockBuilder_CloseAngryMonster(settlers.CustomSettler):
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
		('monster', settlers.Behavior.ANGRY, Point(11, 6)),
		]

class _MockBuilder_CloseAngryMonster2(settlers.CustomSettler):
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
		('monster', settlers.Behavior.ANGRY, Point(4, 4)),
		]

class _MockBuilder_FightingGround(settlers.CustomSettler):
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
		('monster', settlers.Behavior.DUMMY, Point(10, 6)),
		('monster', settlers.Behavior.INERT, Point(9, 4)),
		]

def build(dungeon_id, load_from_reader=None):
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
	return MockGame(rng_seed=0, builders=_DATA[dungeon_id], load_from_reader=load_from_reader)
