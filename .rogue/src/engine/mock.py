from clckwrkbdgr.math import Point, Rect, Size, distance
from clckwrkbdgr.math.grid import Matrix
from . import terrain, actors, items, appliances
from . import builders
from . import scene, events, vision
from . import _base
from .ui import Sprite

### Terrain. ###################################################################

class Void(terrain.Terrain):
	_sprite = Sprite(' ', None)
	_name = 'void'
	_passable = False

class Floor(terrain.Terrain):
	_sprite = Sprite('.', None)
	_name = 'floor'
	_passable = True

class CorridorFloor(terrain.Terrain):
	_sprite = Sprite('.', None)
	_name = 'floor'
	_passable = True
	_allow_diagonal = False

class ToxicWaste(terrain.Terrain):
	_sprite = Sprite('~', None)
	_name = 'toxic waste'
	_passable = True
	def __init__(self, damage=0):
		self.damage = damage
	def load(self, stream):
		self.damage = stream.read_int()
	def save(self, stream):
		super(ToxicWaste, self).save(stream)
		stream.write(self.damage)

class Wall(terrain.Terrain):
	_sprite = Sprite('#', None)
	_name = 'wall'
	_passable = False
	_remembered = Sprite('#', None)

### Items. #####################################################################

class Gold(items.Item):
	_sprite = Sprite('*', None)
	_name = 'gold'

class Potion(items.Item, items.Consumable):
	_sprite = Sprite('!', None)
	_name = 'potion'
	def consume(self, target):
		diff = target.affect_health(+5)
		return [Healed(target, diff)]

class Dagger(items.Item):
	_sprite = Sprite('(', None)
	_name = 'dagger'
	_attack = 1

class Rags(items.Item, items.Wearable):
	_sprite = Sprite('[', None)
	_name = 'rags'
	_protection = 1

class ChainMail(items.Item, items.Wearable):
	_sprite = Sprite('[', None)
	_name = 'chain mail'
	_protection = 3

class ScribbledNote(items.Item):
	_sprite = Sprite('?', None)
	_name = 'note'
	def __init__(self, text='turn around'):
		self.text = text
	def load(self, stream):
		self.text = stream.read()
	def save(self, stream):
		super(ScribbledNote, self).save(stream)
		stream.write(self.text)

### Appliances. ################################################################

class Door(appliances.Appliance):
	_sprite = Sprite('+', None)
	_name = 'door'

class Tree(appliances.Appliance):
	_sprite = Sprite('&', None)
	_name = 'tree'

class StairsUp(appliances.LevelPassage):
	_sprite = Sprite('<', None)
	_name = 'stairs'
	_id = 'enter'
	_can_go_up = True
	_unlocking_item = Gold

class StairsDown(appliances.LevelPassage):
	_sprite = Sprite('>', None)
	_name = 'stairs'
	_id = 'exit'
	_can_go_down = True

class Statue(appliances.Appliance):
	_sprite = Sprite('&', None)
	_name = 'statue'
	_passable = False
	def __init__(self, likeness='dummy'):
		self.likeness = likeness
	def load(self, stream):
		self.likeness = stream.read()
	def save(self, stream):
		super(Statue, self).save(stream)
		stream.write(self.likeness)

### Actors. ####################################################################

class Dragonfly(actors.Actor):
	_sprite = Sprite('d', None)
	_name = 'dragonfly'

class Insect(actors.Behaviour):
	def act(self, game):
		game.fire_event(FlopWings(self))

class Butterfly(actors.Actor, Insect):
	_sprite = Sprite('b', None)
	_name = 'butterfly'
	def __init__(self, *args, **kwargs):
		self.color = kwargs.get('color', 'black')
		if 'color' in kwargs:
			del kwargs['color']
		super(Butterfly, self).__init__(*args, **kwargs)
	def load(self, stream):
		self.color = stream.read()
	def save(self, stream):
		super(Butterfly, self).save(stream)
		stream.write(self.color)

class Rogue(actors.EquippedMonster, actors.Player):
	_hostile_to = [actors.Monster]
	_sprite = Sprite('@', None)
	_name = 'rogue'
	_attack = 1
	_vision = 2
	_max_hp = 10
	_max_inventory = 26

class Rat(actors.Monster, actors.Defensive):
	_hostile_to = [Rogue]
	_sprite = Sprite('r', None)
	_name = 'rat'
	_max_hp = 10
	_attack = 1
	_max_inventory = 1
	_drops = [
			(1, None),
			(5, Potion),
			]

class PackRat(Rat, actors.Defensive):
	_hostile_to = [Rogue]
	_protection = 1
	_max_inventory = 10
	_drops = [
			[
				(6, None),
				(1, Potion),
				],
			[
				(1, Gold),
				],
			]

class Goblin(actors.EquippedMonster, actors.Offensive):
	_hostile_to = [Rogue, PackRat]
	_sprite = Sprite('g', None)
	_name = 'goblin'
	_attack = 1
	_max_hp = 10
	_vision = 4
	_max_inventory = 10

### Events. ####################################################################

class NoFighting(events.Event):
	FIELDS = 'actor other'
class NothingToDrop(events.Event):
	FIELDS = ''
class DropItem(events.Event):
	FIELDS = 'who where what'
class Hit(events.Event):
	FIELDS = ('actor', 'target')
class Healed(events.Event):
	FIELDS = ('target', 'diff')
class FlopWings(events.Event): FIELDS = ('actor')

events.Events.on(Healed)(lambda event: '{0} gains {1}hp.')
events.Events.on(NothingToDrop)(lambda event: 'Nothing to drop.')
events.Events.on(DropItem)(lambda event: '{0} drops {2} on {1}'.format(event.who, event.where, event.what))
events.Events.on(FlopWings)(lambda event: '{0} flops its wings'.format(event.actor))
events.Events.on(_base.Events.Welcome)(lambda *event: '')
events.Events.on(_base.Events.Discover)(lambda *event: '')
class Handler(object):
	@events.Events.on(Hit)
	def handle_hits(self, event):
		return '{0} -> {1}'.format(event.actor, event.target)

### Map. #######################################################################

class MonsterVision(vision.Vision):
	def __init__(self, scene):
		super(MonsterVision, self).__init__(scene)
		self.monster = None
	def is_visible(self, pos):
		return distance(self.monster.pos, pos) <= self.monster.vision
	def visit(self, monster):
		self.monster = monster

class Vision(vision.Vision):
	def __init__(self, scene):
		super(Vision, self).__init__(scene)
		self.visible = Matrix(scene.cells.size, False)
		self.visited = Matrix(scene.cells.size, False)
		self.visible_monsters = []
	def load(self, reader):
		self.visited = reader.read_matrix(lambda c:c=='1')
	def save(self, writer):
		writer.write(self.visited)
	def is_visible(self, pos):
		return self.visible.cell(pos) if self.visible.valid(pos) else False
	def is_explored(self, pos):
		return self.visited.cell(pos) if self.visited.valid(pos) else False
	def iter_important(self):
		return self.visible_monsters
	def visit(self, actor):
		self.visible.clear(False)
		current_visible_monsters = []
		for pos in self.visible:
			if distance(pos, actor.pos) <= actor.vision:
				self.visible.set_cell(pos, True)
				self.visited.set_cell(pos, True)
				for monster in self.scene.iter_actors_at(pos, with_player=False):
					if monster not in self.visible_monsters:
						yield monster
					current_visible_monsters.append(monster)
		self.visible_monsters = current_visible_monsters

class Dungeon(scene.Scene):
	def __init__(self, rng):
		self.rng = rng
		self.cells = None
		self.appliances = []
		self.items = []
		self.monsters = []
	def load(self, reader):
		super(Dungeon, self).load(reader)
		self.cells = reader.read_matrix(terrain.Terrain)
		self.monsters.extend(reader.read_list(actors.Actor))
		self.items.extend(reader.read_list(items.ItemAtPos))
		self.appliances.extend(reader.read_list(appliances.ObjectAtPos))
	def save(self, writer):
		writer.write(self.cells)
		writer.write(self.monsters)
		writer.write(self.items)
		writer.write(sorted(self.appliances))
	def make_vision(self, actor):
		if isinstance(actor, actors.Player):
			return Vision(self)
		return MonsterVision(self)
	def get_area_rect(self): return Rect((0, 0), self.cells.size)
	def generate_dungeon_floor(self):
		builder = DungeonFloor(self.rng, Size(10, 10))
		builder.map_key(**({
			'exit':lambda: StairsDown('tomb', 'enter'),
			}))
		builder.map_key(
				butterfly = lambda pos, color: Butterfly(pos, color=color),
				note = lambda text: ScribbledNote(text),
				)
		return builder
	def generate_tomb(self):
		return Tomb(self.rng, Size(10, 10))
	def generate(self, id):
		if id == 'tomb':
			builder = self.generate_tomb()
		else:
			builder = self.generate_dungeon_floor()
		builder.generate()
		self.cells = builder.make_grid()
		self.appliances = list(builder.make_appliances())
		self.monsters = list(builder.make_actors())
		self.items = list(builder.make_items())
		for _ in range(6):
			builder.point() # Skip not interesting position.
		self._player_pos = builder.point()
	def exit_actor(self, actor):
		self.monsters.remove(actor)
	def enter_actor(self, actor, location):
		location = location or 'enter'
		stairs = next((pos for pos, obj in reversed(self.appliances) if isinstance(obj, appliances.LevelPassage) and obj.id == location), None)
		assert stairs is not None, "No stairs with id {0}".format(repr(location))
		actor.pos = stairs
		self.monsters.append(actor)
	def drop_item(self, item_at_pos):
		self.items.append(item_at_pos)
	def take_item(self, item_at_pos):
		found = next(_ for _ in self.items if _ == item_at_pos)
		self.items.remove(found)
		return found.item
	def rip(self, actor):
		for item in actor.drop_all():
			self.items.append(item)
			yield item.item
		self.monsters.remove(actor)

	def valid(self, pos):
		return self.cells.valid(pos)
	def get_cell_info(self, pos, context=None):
		if not self.cells.valid(pos): # pragma: no cover
			return (None, [], [], [])
		return (
				self.cells.cell(pos),
				list(self.iter_appliances_at(pos)),
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)
	def get_player(self):
		for monster in self.monsters:
			if isinstance(monster, Rogue):
				return monster
	def iter_cells(self, view_rect):
		for y in range(view_rect.height):
			for x in range(view_rect.width):
				pos = view_rect.topleft + Point(x, y)
				yield pos, self.get_cell_info(pos)
	def iter_items_at(self, pos):
		for item_pos, item in self.items:
			if item_pos == pos:
				yield item
	def iter_actors_at(self, pos, with_player=False):
		""" Yield all monsters at given cell. """
		for monster in self.monsters:
			if not with_player and isinstance(monster, Rogue):
				continue
			if monster.pos == pos:
				yield monster
	def iter_actors_in_rect(self, rect):
		for monster in self.monsters:
			if not rect.contains(monster.pos, with_border=True):
				continue
			yield monster
	def iter_appliances_at(self, pos):
		for obj_pos, obj in self.appliances:
			if obj_pos == pos:
				yield obj
	def iter_active_monsters(self):
		return self.monsters

### Builders. ##################################################################

class Tomb(builders.Builder):
	class Mapping:
		@staticmethod
		def start(): return StairsUp('floor', 'exit')
		wall = Wall()
		void = Void()
		_ = {
			'corridor_floor': CorridorFloor(),
			'floor': Floor(),
			'water': ToxicWaste(),
			}

	def fill_grid(self, grid):
		import textwrap
		strmap = textwrap.dedent("""\
				###   
				#~####
				#....#
				####.#
				   #.#
				   ###
				""").splitlines()
		grid.clear('void')
		for y, row in enumerate(strmap):
			for x, c in enumerate(row):
				if c == '#':
					grid.set_cell((x, y), 'wall')
				elif c == '~':
					self._start = Point(x, y)
					grid.set_cell((x, y), 'water')
				elif c == '.':
					grid.set_cell((x, y), 'corridor_floor')
	def generate_appliances(self):
		yield self._start, 'start'

class DungeonFloor(builders.Builder):
	class Mapping:
		wall = Wall()
		_ = {
			'floor': Floor(),
			'water': ToxicWaste(),
			}
		@staticmethod
		def start(): return StairsUp()
		@staticmethod
		def statue(likeness): return Statue(likeness)

		rat = Rat
		dragonfly = Dragonfly
		goblin = Goblin
		healing_potion = Potion

	def is_open(self, pos):
		return self.grid.cell(pos) == 'floor'

	def fill_grid(self, grid):
		for x in range(self.size.width):
			grid.set_cell((x, 0), 'wall')
			grid.set_cell((x, self.size.height - 1), 'wall')
		for y in range(self.size.height):
			grid.set_cell((0, y), 'wall')
			grid.set_cell((self.size.width - 1, y), 'wall')
		for x in range(1, self.size.width - 1):
			for y in range(1, self.size.height - 1):
				grid.set_cell((x, y), 'floor')
		obstacle_pos = self.point_in_rect(Rect((0, 0), self.size))
		grid.set_cell(obstacle_pos, 'wall')
		obstacle_pos = self.point()
		grid.set_cell(obstacle_pos, 'water')
	def generate_appliances(self):
		yield self.point(self.is_accessible), 'start'
		yield self.point(self.is_accessible), 'exit'
		yield self.point(self.is_accessible), 'statue', 'goddess'
	def generate_actors(self):
		yield self.point(self.is_free), 'butterfly', 'red'
	def generate_items(self):
		yield self.point(self.is_accessible), 'note', 'welcome'

class Squat(DungeonFloor):
	CELLS_PER_MONSTER = 60 # One monster for every 60 cells.
	CELLS_PER_ITEM = 180 # One item for every 180 cells.
	PASSABLE = ('floor',)
	DISTRIBUTION = None
	def generate_actors(self):
		""" Places random population of different types of monsters.
		"""
		for _ in self.distribute(self.DISTRIBUTION, self.MONSTERS, self.amount_by_free_cells(self.CELLS_PER_MONSTER)):
			yield _
	def generate_items(self):
		""" Drops items in random locations. """
		for _ in self.distribute(self.DISTRIBUTION, self.ITEMS, self.amount_by_free_cells(self.CELLS_PER_ITEM)):
			yield _

class UniformSquat(Squat):
	MONSTERS = [
			('dragonfly',),
			('goblin',),
			('rat',),
			]
	ITEMS = [
			('healing_potion',),
			]
	DISTRIBUTION = builders.UniformDistribution

class WeightedSquat(Squat):
	MONSTERS = [
			(1, ('dragonfly',)),
			(5, ('goblin',)),
			(10, ('rat',)),
			]
	ITEMS = [
			(1, ('healing_potion',)),
			]
	DISTRIBUTION = builders.WeightedDistribution

### Game. ######################################################################

class NanoDungeon(_base.Game):
	def __init__(self, rng_seed=0):
		super(NanoDungeon, self).__init__(rng_seed)
	def make_player(self):
		rogue = Rogue(None)
		rogue.grab(Dagger())
		return rogue
	def make_scene(self, scene_id):
		return Dungeon(self.rng)
