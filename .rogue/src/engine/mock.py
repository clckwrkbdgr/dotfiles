from clckwrkbdgr.math import Point, Rect
from clckwrkbdgr.math.grid import Matrix
from . import terrain, actors, items, appliances
from . import builders
from . import scene, events

class Floor(terrain.Terrain):
	_sprite = '.'
	_name = 'floor'

class SoftFloor(terrain.Terrain):
	_sprite = '.'
	_name = 'soft floor'
	def __init__(self, softness=0):
		self.softness = softness
	def load(self, stream):
		self.softness = stream.read_int()
	def save(self, stream):
		super(SoftFloor, self).save(stream)
		stream.write(self.softness)

class MockFloor(terrain.Terrain):
	_sprite = '.'
	_name = 'floor'

class MockWall(terrain.Terrain):
	_sprite = '#'
	_name = 'wall'

class MockGoblin(actors.Monster):
	_sprite = 'g'
	_name = 'goblin'

class MockGold(items.Item):
	_sprite = '*'
	_name = 'gold'

class MockDoor(appliances.Appliance):
	_sprite = '+'
	_name = 'door'

class MockPotion(items.Item):
	_sprite = '!'
	_name = 'potion'

class Dagger(items.Item):
	_sprite = '('
	_name = 'dagger'

class Rags(items.Item, items.Wearable):
	_sprite = '['
	_name = 'rags'

class McGuffin(items.Item):
	_sprite = '*'
	_name = 'mcguffin'

class MockPotion(items.Item):
	_sprite = '!'
	_name = 'potion'

class ColoredPotion(items.Item):
	_sprite = '.'
	_name = 'potion'
	def __init__(self, color='transparent'):
		self.color = color
	def load(self, stream):
		self.color = stream.read()
	def save(self, stream):
		super(ColoredPotion, self).save(stream)
		stream.write(self.color)

class MockActor(actors.Actor):
	_sprite = '@'
	_name = 'rogue'

class Rat(actors.Monster):
	_sprite = 'r'
	_name = 'rat'
	_max_hp = 10
	_drops = [
			(1, None),
			(5, MockPotion),
			]

class PackRat(Rat):
	_drops = [
			[
				(6, None),
				(1, MockPotion),
				],
			[
				(1, McGuffin),
				],
			]

class Goblin(actors.EquippedMonster):
	_sprite = 'g'
	_name = 'goblin'
	_max_hp = 10

class ColoredMonster(actors.Monster):
	def __init__(self, *args, **kwargs):
		self.color = kwargs.get('color')
		if 'color' in kwargs:
			del kwargs['color']
		super(ColoredMonster, self).__init__(*args, **kwargs)
	def load(self, stream):
		super(ColoredMonster, self).load(stream)
		self.color = stream.read()
	def save(self, stream):
		super(ColoredMonster, self).save(stream)
		stream.write(self.color)

class MockStairs(appliances.Appliance):
	_sprite = '>'
	_name = 'stairs'

class ColoredDoor(appliances.Appliance):
	_sprite = '+'
	_name = 'door'
	def __init__(self, color='transparent'):
		self.color = color
	def load(self, stream):
		self.color = stream.read()
	def save(self, stream):
		super(ColoredDoor, self).save(stream)
		stream.write(self.color)

class EmptyEvent(events.Event):
	FIELDS = ''
class MockEvent(events.Event):
	FIELDS = 'who where what'
class MockOtherEvent(events.Event):
	FIELDS = ('actor', 'target')

events.Events.on(EmptyEvent)(lambda event: '...')
events.Events.on(MockEvent)(lambda event: '{0} stands {1} wielding {2}'.format(event.who, event.where, event.what))
class Handler(object):
	@events.Events.on(MockOtherEvent)
	def handle_other_event(self, event):
		return '{0} -> {1}'.format(event.actor, event.target)

class MockScene(scene.Scene):
	def __init__(self):
		self.cells = Matrix((10, 10), MockFloor())
		for x in range(10):
			self.cells.set_cell((x, 0), MockWall())
			self.cells.set_cell((x, 9), MockWall())
		for y in range(10):
			self.cells.set_cell((0, y), MockWall())
			self.cells.set_cell((9, y), MockWall())
		self.appliances = [appliances.ObjectAtPos(Point(5, 5), MockDoor())]
		self.items = [items.ItemAtPos(Point(5, 6), MockGold())]
		self.monsters = [MockGoblin(Point(6, 5))]
	def get_cell_info(self, pos, context=None):
		return (
				self.cells.cell(pos),
				list(self.iter_appliances_at(pos)),
				list(self.iter_items_at(pos)),
				list(self.iter_actors_at(pos, with_player=True)),
				)
	def iter_cells(self, view_rect): # pragma: no cover
		for y in range(view_rect.height):
			for x in range(view_rect.width):
				pos = view_rect.topleft + Point(x, y)
				yield pos, self.get_cell_info(pos)
	def iter_items_at(self, pos): # pragma: no cover
		for item_pos, item in self.items:
			if item_pos == pos:
				yield item
	def iter_actors_at(self, pos, with_player=False): # pragma: no cover
		""" Yield all monsters at given cell. """
		for monster in self.monsters:
			if monster.pos == pos:
				yield monster
	def iter_appliances_at(self, pos): # pragma: no cover
		for obj_pos, obj in self.appliances:
			if obj_pos == pos:
				yield obj

class MockBuilder(builders.Builder):
	class Mapping:
		wall = '#'
		_ = {
			'floor': '.',
			'water': '~',
			}
		@staticmethod
		def start(): return 'start'
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
	def generate_actors(self):
		yield self.point(self.is_free), 'monster', 'angry'
	def generate_items(self):
		yield self.point(self.is_accessible), 'item', 'mcguffin'

class MockSquatters(MockBuilder):
	class Mapping:
		rodent = staticmethod(lambda pos,*data: ('rodent',) + data + (pos,))
		plant = staticmethod(lambda pos,*data: ('plant',) + data + (pos,))
		slime = staticmethod(lambda pos,*data: ('slime',) + data + (pos,))
		healing_potion = staticmethod(lambda *data: ('healing potion',) + data)
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

class UniformSquatters(MockSquatters):
	MONSTERS = [
			('plant',),
			('slime',),
			('rodent',),
			]
	ITEMS = [
			('healing_potion',),
			]
	DISTRIBUTION = builders.UniformDistribution

class WeightedSquatters(MockSquatters):
	MONSTERS = [
			(1, ('plant',)),
			(5, ('slime',)),
			(10, ('rodent',)),
			]
	ITEMS = [
			(1, ('healing_potion',)),
			]
	DISTRIBUTION = builders.WeightedDistribution
