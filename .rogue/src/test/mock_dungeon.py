from clckwrkbdgr.math import Point
from .. import pcg as builders
from .. import pcg as settlers
from .. import monsters
from .. import game
from ..engine.terrain import Terrain
from ..engine import items

class NameItem(items.Item):
	_name = 'name'
	_sprite = '!'

class Potion(items.Item):
	_name = 'potion'
	_sprite = '!'

class HealingPotion(items.Item, game.Consumable):
	_name = 'healing potion'
	_sprite = '!'
	def apply_effect(self, game, monster):
		game.affect_health(monster, +5)

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

class Name(monsters.Monster):
	_name = 'name'
	_sprite = 'M'
	_max_hp = 100
	_vision = 10
	_drops = [
			(1, Money),
			(2, Potion),
			]

class Player(game.Player):
	_name = 'player'
	_sprite = '@'
	_max_hp = 10
	_vision = 10
	_drops = None

class Monster(monsters.Monster):
	_name = 'monster'
	_sprite = 'M'
	_max_hp = 3
	_vision = 10
	_drops = None

class AngryMonster(monsters.Angry):
	_name = 'monster'
	_sprite = 'M'
	_max_hp = 3
	_vision = 10
	_drops = None

class InertMonster(monsters.Inert):
	_name = 'monster'
	_sprite = 'M'
	_max_hp = 3
	_vision = 10
	_drops = None

class DummyThief(monsters.Monster):
	_name = 'thief'
	_sprite = 'T'
	_max_hp = 3
	_vision = 10
	_drops = [
			(1, Money),
			]

class Thief(monsters.Angry):
	_name = 'thief'
	_sprite = 'T'
	_max_hp = 3
	_vision = 10
	_drops = [
			(1, Money),
			]

class NameTerrain(Terrain):
	_name = 'name'
	_sprite = '.'
class Space(Terrain):
	_name = ' '
	_sprite = ' '
	_passable = False
class Wall(Terrain):
	_name = '#'
	_sprite = "#"
	_passable = False
	_remembered='#'
class Floor(Terrain):
	_name = '.'
	_sprite = "."
	_passable = True
class Water(Terrain):
	_name = '~'
	_sprite = "."
	_passable = True
	_allow_diagonal=False
class NonDiagonalWall(Terrain):
	_name = '#'
	_sprite = "#"
	_passable = True
	_remembered='#'
	_allow_diagonal=False
	_dark=True
class NonDiagonalOblivionWall(Terrain):
	_name = '#'
	_sprite = "#"
	_passable = True
	_allow_diagonal=False
	_dark=True
class Corner(Terrain):
	_name = '+'
	_sprite = "+"
	_passable = False
	_remembered='+'
class WallH(Terrain):
	_name = '-'
	_sprite = "-"
	_passable = False
	_remembered='-'
class WallV(Terrain):
	_name = '|'
	_sprite = "|"
	_passable = False
	_remembered='|'
class DarkFloor(Terrain):
	_name = '^'
	_sprite = "^"
	_passable = True
	_remembered='^'
	_allow_diagonal=False
	_dark=True

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
	def angry_monster(pos,*data):
		return AngryMonster(*(data + (pos,)))
	@staticmethod
	def inert_monster(pos,*data):
		return InertMonster(*(data + (pos,)))
	@staticmethod
	def thief(pos,*data):
		return Thief(*(data + (pos,)))
	@staticmethod
	def dummy_thief(pos,*data):
		return DummyThief(*(data + (pos,)))
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
	MONSTER = ('thief',)

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
	MONSTER = ('angry_monster',)

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
			(Point(2, 5), 'monster',),
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
		(Point(1, 1), 'monster',),
		(Point(1, 6), 'monster',),
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
		(Point(1, 1), 'monster',),
		(Point(1, 6), 'monster',),
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
		(Point(10, 6), 'monster',),
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
		(Point(10, 6), 'dummy_thief'),
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
		(Point(10, 6), 'inert_monster',),
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
		(Point(11, 6), 'angry_monster',),
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
		(Point(4, 4), 'angry_monster',),
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
		(Point(10, 6), 'monster',),
		(Point(9, 4), 'inert_monster',),
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
