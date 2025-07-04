from clckwrkbdgr.math import Point
from .. import pcg as builders
from .. import pcg as settlers
from .. import terrain, items, monsters
from .. import game

class Name(monsters.Monster):
	_name = 'name'
	_sprite = 'M'
	max_hp = 100
	vision = 10
	drops = [
			(1, 'money'),
			(2, 'potion'),
			]

class Player(monsters.Monster):
	_name = 'player'
	_sprite = '@'
	max_hp = 10
	vision = 10
	drops = None

class Monster(monsters.Monster):
	_name = 'monster'
	_sprite = 'M'
	max_hp = 3
	vision = 10
	drops = None

class Thief(monsters.Monster):
	_name = 'thief'
	_sprite = 'T'
	max_hp = 3
	vision = 10
	drops = [
			(1, 'money'),
			]

class NameItem(items.Item):
	_name = 'name'
	_sprite = '!'

class Potion(items.Item):
	_name = 'potion'
	_sprite = '!'

class HealingPotion(items.Item):
	_name = 'healing potion'
	_sprite = '!'
	effect = items.Effect.HEALING

class Money(items.Item):
	_name = 'money'
	_sprite = '$'

class Weapon(items.Item):
	_name = 'weapon'
	_sprite = '('

class Ranged(items.Item):
	_name = 'ranged'
	_sprite = ')'

class Rags(items.Item):
	_name = 'rags'
	_sprite = '['

class NameTerrain(terrain.Cell):
	_name = 'name'
	_sprite = '.'
class Space(terrain.Cell):
	_name = ' '
	_sprite = ' '
	passable = False
class Wall(terrain.Cell):
	_name = '#'
	_sprite = "#"
	passable = False
	remembered='#'
class Floor(terrain.Cell):
	_name = '.'
	_sprite = "."
	passable = True
class Water(terrain.Cell):
	_name = '~'
	_sprite = "."
	passable = True
	allow_diagonal=False
class NonDiagonalWall(terrain.Cell):
	_name = '#'
	_sprite = "#"
	passable = True
	remembered='#'
	allow_diagonal=False
	dark=True
class NonDiagonalOblivionWall(terrain.Cell):
	_name = '#'
	_sprite = "#"
	passable = True
	allow_diagonal=False
	dark=True
class Corner(terrain.Cell):
	_name = '+'
	_sprite = "+"
	passable = False
	remembered='+'
class WallH(terrain.Cell):
	_name = '-'
	_sprite = "-"
	passable = False
	remembered='-'
class WallV(terrain.Cell):
	_name = '|'
	_sprite = "|"
	passable = False
	remembered='|'
class DarkFloor(terrain.Cell):
	_name = '^'
	_sprite = "^"
	passable = True
	remembered='^'
	allow_diagonal=False
	dark=True

class MockGame(game.Game):
	SPECIES = {
			'name' : Name,
			'player' : Player,
			'monster' : Monster,
			'thief' : Thief,
			'Name' : Name,
			'Player' : Player,
			'Monster' : Monster,
			'Thief' : Thief,
			}
	ITEMS = {
			'name' : NameItem,
			'potion' : Potion,
			'healing_potion' : HealingPotion,
			'money' : Money,
			'weapon' : Weapon,
			'ranged' : Ranged,
			'rags' : Rags,
			'NameItem' : NameItem,
			'Potion' : Potion,
			'HealingPotion' : HealingPotion,
			'Money' : Money,
			'Weapon' : Weapon,
			'Ranged' : Ranged,
			'Rags' : Rags,
			}
	TERRAIN = {
		None : Space,
		'name' : NameTerrain,
		' ' : Space,
		'#' : Wall,
		'.' : Floor,
		'~' : Water,
		'NameTerrain' : NameTerrain,
		'Space' : Space,
		'Wall' : Wall,
		'Floor' : Floor,
		'Water' : Water,
		# Rogue dungeon:
		'*' : NonDiagonalWall,
		'%' : NonDiagonalOblivionWall,
		'+' : Corner,
		'-' : WallH,
		'|' : WallV,
		'^' : DarkFloor,
		'NonDiagonalWall' : NonDiagonalWall,
		'NonDiagonalOblivionWall' : NonDiagonalOblivionWall,
		'Corner' : Corner,
		'WallH' : WallH,
		'WallV' : WallV,
		'DarkFloor' : DarkFloor,
		}

class MockMapping:
	_ = {_key:_item() for (_key, _item) in MockGame.TERRAIN.items()}
	@staticmethod
	def start(): return 'start'
	@staticmethod
	def exit(): return 'exit'
	@staticmethod
	def monster(pos,*data):
		return Monster(*(data + (pos,)))
	@staticmethod
	def thief(pos,*data):
		return Thief(*(data + (pos,)))
	@staticmethod
	def potion(*data):
		return Potion(*data)
	@staticmethod
	def healing_potion(*data):
		return HealingPotion(*data)

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
