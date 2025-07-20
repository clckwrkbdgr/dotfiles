from clckwrkbdgr import unittest
from .. import scene
from clckwrkbdgr.math import Matrix, Point, Rect
from .. import terrain, actors, items, appliances

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

class TestActors(unittest.TestCase):
	def should_str_cells(self):
		scene = MockScene()
		self.assertEqual(scene.str_cell((0, 0)), '#')
		self.assertEqual(scene.str_cell((1, 1)), '.')
		self.assertEqual(scene.str_cell((5, 5)), '+')
		self.assertEqual(scene.str_cell((5, 6)), '*')
		self.assertEqual(scene.str_cell((6, 5)), 'g')
	def should_str_scene(self):
		scene = MockScene()
		self.assertEqual(scene.tostring(Rect((0, 0), scene.cells.size)), unittest.dedent("""\
				##########
				#........#
				#........#
				#........#
				#........#
				#....+g..#
				#....*...#
				#........#
				#........#
				##########
				"""))
	def should_str_only_part_of_scene(self):
		scene = MockScene()
		self.assertEqual(scene.tostring(Rect((3, 3), (7, 4))), unittest.dedent("""\
				......#
				......#
				..+g..#
				..*...#
				"""))
