from clckwrkbdgr.math import Point
from .. import pcg as builders
from .. import pcg as settlers
from .. import game
from ..engine.terrain import Terrain
from ..engine import items, actors
from ..engine.ui import Sprite

class NameItem(items.Item):
	_name = 'name'
	_sprite = Sprite('!', None)

class Potion(items.Item):
	_name = 'potion'
	_sprite = Sprite('!', None)

class HealingPotion(items.Item, items.Consumable):
	_name = 'healing potion'
	_sprite = Sprite('!', None)
	def consume(self, target):
		diff = target.affect_health(+5)
		return [game.HealthEvent(target, diff)]

class Money(items.Item):
	_name = 'money'
	_sprite = Sprite('$', None)

class Weapon(items.Item):
	_name = 'weapon'
	_sprite = Sprite('(', None)

class Ranged(items.Item):
	_name = 'ranged'
	_sprite = Sprite(')', None)

class Rags(items.Item):
	_name = 'rags'
	_sprite = Sprite('[', None)

class Name(actors.EquippedMonster):
	_name = 'name'
	_sprite = Sprite('M', None)
	_max_hp = 100
	_vision = 10
	_drops = [
			(1, Money),
			(2, Potion),
			]

class Player(game.Player):
	_hostile_to = [actors.Monster]
	_name = 'player'
	_sprite = Sprite('@', None)
	_max_hp = 10
	_vision = 10
	_attack = 1
	_max_inventory = 26
	_drops = None

class MockMonster(actors.EquippedMonster):
	_hostile_to = [Player]
	_name = 'monster'
	_sprite = Sprite('M', None)
	_max_hp = 3
	_vision = 10
	_attack = 1
	_max_inventory = 5
	_drops = None

class AngryMonster(game.Angry):
	_hostile_to = [Player]
	_name = 'monster'
	_sprite = Sprite('M', None)
	_max_hp = 3
	_vision = 10
	_attack = 1
	_max_inventory = 5
	_drops = None

class InertMonster(game.Inert):
	_hostile_to = [Player]
	_name = 'monster'
	_sprite = Sprite('M', None)
	_max_hp = 3
	_vision = 10
	_attack = 1
	_max_inventory = 5
	_drops = None

class DummyThief(actors.EquippedMonster):
	_hostile_to = [Player]
	_name = 'thief'
	_sprite = Sprite('T', None)
	_max_hp = 3
	_vision = 10
	_attack = 1
	_max_inventory = 5
	_drops = [
			(1, Money),
			]

class Thief(game.Angry):
	_hostile_to = [Player]
	_name = 'thief'
	_sprite = Sprite('T', None)
	_max_hp = 3
	_vision = 10
	_attack = 1
	_max_inventory = 5
	_drops = [
			(1, Money),
			]

class NameTerrain(Terrain):
	_name = 'name'
	_sprite = Sprite('.', None)
class Space(Terrain):
	_name = ' '
	_sprite = Sprite(' ', None)
	_passable = False
class Wall(Terrain):
	_name = '#'
	_sprite = Sprite("#", None)
	_passable = False
	_remembered= Sprite('#', None)
class Floor(Terrain):
	_name = '.'
	_sprite = Sprite(".", None)
	_passable = True
class Water(Terrain):
	_name = '~'
	_sprite = Sprite(".", None)
	_passable = True
	_allow_diagonal=False
class NonDiagonalWall(Terrain):
	_name = '#'
	_sprite = Sprite("#", None)
	_passable = True
	_remembered=Sprite('#', None)
	_allow_diagonal=False
	_dark=True
class NonDiagonalOblivionWall(Terrain):
	_name = '#'
	_sprite = Sprite("#", None)
	_passable = True
	_allow_diagonal=False
	_dark=True
class Corner(Terrain):
	_name = '+'
	_sprite = Sprite("+", None)
	_passable = False
	_remembered=Sprite('+', None)
class WallH(Terrain):
	_name = '-'
	_sprite = Sprite("-", None)
	_passable = False
	_remembered=Sprite('-', None)
class WallV(Terrain):
	_name = '|'
	_sprite = Sprite("|", None)
	_passable = False
	_remembered=Sprite('|', None)
class DarkFloor(Terrain):
	_name = '^'
	_sprite = Sprite("^", None)
	_passable = True
	_remembered=Sprite('^', None)
	_allow_diagonal=False
	_dark=True

class MockStairs(game.LevelExit):
	_name = 'stairs'
	_sprite = Sprite('>', None)

class MockGame(game.Game):
	PLAYER_CLASS = Player
	def get_player(self): # TODO shortcut for testing purposes.
		return self.scene.get_player()

class MockMapping:
	_ = {
		None : Space(),
		'name' : NameTerrain(),
		' ' : Space(),
		'#' : Wall(),
		'.' : Floor(),
		'~' : Water(),
		'NameTerrain' : NameTerrain(),
		'Space' : Space(),
		'Wall' : Wall(),
		'Floor' : Floor(),
		'Water' : Water(),
		# Rogue dungeon:
		'*' : NonDiagonalWall(),
		'%' : NonDiagonalOblivionWall(),
		'+' : Corner(),
		'-' : WallH(),
		'|' : WallV(),
		'^' : DarkFloor(),
		'NonDiagonalWall' : NonDiagonalWall(),
		'NonDiagonalOblivionWall' : NonDiagonalOblivionWall(),
		'Corner' : Corner(),
		'WallH' : WallH(),
		'WallV' : WallV(),
		'DarkFloor' : DarkFloor(),
		}
	@staticmethod
	def start(): return 'start'
	@staticmethod
	def exit(): return MockStairs()
	@staticmethod
	def monster(pos,*data):
		return MockMonster(*(data + (pos,)))
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

class _MockBuilderSingleMockThief(settlers.CustomMap):
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
	def is_open(self, pos): return self.grid.cell(pos) == '.'
	def generate_actors(self): yield (self.point(self.is_free), 'thief')

class _MockBuilderSingleMockMonster(settlers.CustomMap):
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
	def is_open(self, pos): return self.grid.cell(pos) == '.'
	def generate_actors(self): yield (self.point(self.is_free), 'angry_monster')

class CustomSettler(settlers.CustomMap):
	""" Fills map with predetermined monsters and items.
	Data should be provided as list of raw parameters:
	(<item/monster data>, <pos>)
	"""
	MONSTERS = [
			]
	ITEMS = [
			]
	def generate_actors(self):
		self.rng.choice([1]) # FIXME mock action just to shift RNG
		for _ in self.MONSTERS:
			yield _
	def generate_items(self):
		for _ in self.ITEMS:
			yield _

class _MockBuilder_PotionsLyingAround(CustomSettler):
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

class _MockBuilder_MockSettler(CustomSettler):
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

class _MockBuilderUnSettler(CustomSettler):
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

class _MockBuilder_NowYouSeeMe(CustomSettler):
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

class _MockMiniRogueBuilderUnSettler(CustomSettler):
	Mapping = MockMapping
	MAP_DATA = """\
		  +--+ % 
		* |@.| % 
		**^..^%% 
		  |.>|   
		  +--+   
		"""

class _MockMiniBuilderUnSettler(CustomSettler):
	Mapping = MockMapping
	MAP_DATA = """\
		@#..#
		~#..#
		~~.>#
		#####
		"""

class _MockBuilder_MonstersOnTopOfItems(CustomSettler):
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

class _MockBuilder_CloseMonster(CustomSettler):
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

class _MockBuilder_CloseThief(CustomSettler):
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

class _MockBuilder_CloseInertMonster(CustomSettler):
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

class _MockBuilder_CloseAngryMonster(CustomSettler):
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

class _MockBuilder_CloseAngryMonster2(CustomSettler):
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

class _MockBuilder_FightingGround(CustomSettler):
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

class _MockBuilder_NowYouSeeMeGame(MockGame): BUILDERS = [_MockBuilder_NowYouSeeMe]
class _MockMiniRogueBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniRogueBuilderUnSettler]
class _MockBuilderUnSettlerGame(MockGame): BUILDERS = [_MockBuilderUnSettler]
class _MockBuilder_MonstersOnTopOfItemsGame(MockGame): BUILDERS = [_MockBuilder_MonstersOnTopOfItems]
class _MockMiniBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniBuilderUnSettler]
class _MockMiniBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniBuilderUnSettler]
class _MockMiniBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniBuilderUnSettler]
class _MockMiniBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniBuilderUnSettler]
class _MockMiniBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniBuilderUnSettler]
class _MockBuilder_NowYouSeeMeGame(MockGame): BUILDERS = [_MockBuilder_NowYouSeeMe]
class _MockMiniBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniBuilderUnSettler]
class _MockMiniRogueBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniRogueBuilderUnSettler]
class _MockMiniRogueBuilderUnSettlerGame(MockGame): BUILDERS = [_MockMiniRogueBuilderUnSettler]
class _MockBuilder_PotionsLyingAroundGame(MockGame): BUILDERS = [_MockBuilder_PotionsLyingAround]
class _MockBuilder_CloseMonsterGame(MockGame): BUILDERS = [_MockBuilder_CloseMonster]
class _MockBuilder_CloseThiefGame(MockGame): BUILDERS = [_MockBuilder_CloseThief]
class _MockBuilder_CloseInertMonsterGame(MockGame): BUILDERS = [_MockBuilder_CloseInertMonster]
class _MockBuilder_CloseAngryMonsterGame(MockGame): BUILDERS = [_MockBuilder_CloseAngryMonster]
class _MockBuilder_CloseAngryMonster2Game(MockGame): BUILDERS = [_MockBuilder_CloseAngryMonster2]
class _MockBuilderSingleMockMonsterGame(MockGame): BUILDERS = [_MockBuilderSingleMockMonster]
class _MockBuilderSingleMockThiefGame(MockGame): BUILDERS = [_MockBuilderSingleMockThief]
class _MockBuilder_MockSettlerGame(MockGame): BUILDERS = [_MockBuilder_MockSettler]
class _MockBuilder_MockSettlerGame(MockGame): BUILDERS = [_MockBuilder_MockSettler]
class _MockBuilder_FightingGroundGame(MockGame): BUILDERS = [_MockBuilder_FightingGround]
class _MockBuilder_PotionsLyingAroundGame(MockGame): BUILDERS = [_MockBuilder_PotionsLyingAround]
class _MockBuilder_MockSettlerGame(MockGame): BUILDERS = [_MockBuilder_MockSettler]

def build(dungeon_id):
	_DATA = {
			'now you see me': _MockBuilder_NowYouSeeMeGame,
			'mini dark rogue': _MockMiniRogueBuilderUnSettlerGame,
			'lonely': _MockBuilderUnSettlerGame,
			'monsters on top': _MockBuilder_MonstersOnTopOfItemsGame,
			'mini lonely': _MockMiniBuilderUnSettlerGame,
			'mini 2 lonely': _MockMiniBuilderUnSettlerGame,
			'mini 3 lonely': _MockMiniBuilderUnSettlerGame,
			'mini 4 lonely': _MockMiniBuilderUnSettlerGame,
			'mini 5 lonely': _MockMiniBuilderUnSettlerGame,
			'mini 6 monster': _MockBuilder_NowYouSeeMeGame,
			'mini 6 lonely': _MockMiniBuilderUnSettlerGame,
			'mini rogue 2 lonely': _MockMiniRogueBuilderUnSettlerGame,
			'mini rogue lonely': _MockMiniRogueBuilderUnSettlerGame,
			'potions lying around': _MockBuilder_PotionsLyingAroundGame,
			'close monster': _MockBuilder_CloseMonsterGame,
			'close thief': _MockBuilder_CloseThiefGame,
			'close inert monster': _MockBuilder_CloseInertMonsterGame,
			'close angry monster': _MockBuilder_CloseAngryMonsterGame,
			'close angry monster 2': _MockBuilder_CloseAngryMonster2Game,
			'single mock monster': _MockBuilderSingleMockMonsterGame,
			'single mock thief': _MockBuilderSingleMockThiefGame,
			'mock settler': _MockBuilder_MockSettlerGame,
			'mock settler restored': _MockBuilder_MockSettlerGame,
			'fighting around': _MockBuilder_FightingGroundGame,
			'potions lying around 2': _MockBuilder_PotionsLyingAroundGame,
			'monster and potion': _MockBuilder_MockSettlerGame,
			}
	game = _DATA[dungeon_id](rng_seed=0)
	game.generate()
	return game
