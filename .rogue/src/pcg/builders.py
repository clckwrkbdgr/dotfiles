import textwrap
from clckwrkbdgr.math import Matrix, Point, Size
import logging
Log = logging.getLogger('rogue')
from clckwrkbdgr import pcg
import clckwrkbdgr.pcg.cellular
import clckwrkbdgr.pcg.maze
import clckwrkbdgr.pcg.rogue
from clckwrkbdgr.pcg import bsp
import clckwrkbdgr.math
from ..engine import builders

class Builder(object):
	""" Base class to build terrain matrix
	with start pos and exit pos
	and to populate terrain with monsters and other objects.

	Override method _build() to produce actual terrain.
	Override methods _populate() and _place_items() to do actual jobs.
	"""
	def __init__(self, rng, map_size):
		""" Initializes builder with given RNG and map size.
		To actually create and fill map call build().
		"""
		self.builder = builders.Builder(rng, map_size)
		self.strata = None
		self.start_pos = None
		self.exit_pos = None
	def build(self):
		""" Creates empty terrain matrix
		and calls custom _build() to fill it.
		Usually matrix cells are not real Terrains,
		but IDs of the terrain types available in the custom Game definitions
		and should be replaced later with actual Terrain in the Game class itself.

		Places monsters, items and other objects all over map, according to custom overrides.
		Creates list .monsters with data for each monster in form of tuple: (pos, ...other data).
		Creates list .items with data for each item in form of tuple: (pos, ...other data).
		Values should be replaced later with actual objects in the Game class itself.
		"""
		self.strata = Matrix(self.builder.size, None)
		self._build()
		self.monsters = []
		self._populate()
		self.items = []
		self._place_items()
	def _build(self): # pragma: no cover
		""" Should fill self.strata, self.start_pos and self.exit_pos. """
		raise NotImplementedError()
	def _populate(self): # pragma: no cover
		""" Should fill array of .monsters """
		pass
	def _place_items(self): # pragma: no cover
		""" Should fill array of .items
		Default implementation places no items.
		"""
		pass

class CustomMap(Builder):
	""" Builds map described by custom layout.
	Forces map size to fit given layout instead of considering passed parameter.
	Set .MAP_DATA to multiline string (one char for each cell)
	OR
	pass it instead of map_size parameter.
	Dedent is performed automatically.
	Set char to '@' to indicate start pos.
	Set char to '>' to indicate exit pos.
	Set field .ENTER_TERRAIN and/or .EXIT_TERRAIN to use as terrain for those cells.
	Default is '.' for both.
	"""
	ENTER_TERRAIN = '.'
	EXIT_TERRAIN = '.'
	def __init__(self, rng, map_size):
		if hasattr(self, 'MAP_DATA'):
			self._map_data = self.MAP_DATA
		elif isinstance(map_size, str):
			self._map_data = map_size
		self._map_data = textwrap.dedent(self._map_data).splitlines()
		map_size = Size(len(self._map_data[0]), len(self._map_data))
		super(CustomMap, self).__init__(rng, map_size)
	def _build(self):
		for x in range(self.builder.size.width):
			for y in range(self.builder.size.height):
				if self._map_data[y][x] == '@':
					self.start_pos = Point(x, y)
					self.strata.set_cell((x, y), self.ENTER_TERRAIN)
				elif self._map_data[y][x] == '>':
					self.exit_pos = Point(x, y)
					self.strata.set_cell((x, y), self.EXIT_TERRAIN)
				else:
					self.strata.set_cell((x, y), self._map_data[y][x])

class RogueDungeon(Builder):
	""" Original Rogue dungeon.
	3x3 rooms connected by rectangular tunnels.
	"""
	def _build(self):
		builder = clckwrkbdgr.pcg.rogue.Dungeon(self.builder.rng, self.builder.size, Size(3, 3), Size(4, 4))
		builder.generate_rooms()
		builder.generate_maze()
		builder.generate_tunnels()

		for room in builder.iter_rooms():
			self.strata.set_cell((room.topleft.x, room.topleft.y), 'corner')
			self.strata.set_cell((room.topleft.x, room.topleft.y+room.size.height), 'corner')
			self.strata.set_cell((room.topleft.x+room.size.width, room.topleft.y), 'corner')
			self.strata.set_cell((room.topleft.x+room.size.width, room.topleft.y+room.size.height), 'corner')
			for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
				self.strata.set_cell((x, room.topleft.y), 'wall_h')
				self.strata.set_cell((x, room.topleft.y+room.size.height), 'wall_h')
			for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
				self.strata.set_cell((room.topleft.x, y), 'wall_v')
				self.strata.set_cell((room.topleft.x+room.size.width, y), 'wall_v')
			for y in range(room.topleft.y+1, room.topleft.y+room.size.height):
				for x in range(room.topleft.x+1, room.topleft.x+room.size.width):
					self.strata.set_cell((x, y), 'floor')

		for tunnel in builder.iter_tunnels():
			for cell in tunnel.iter_points():
				self.strata.set_cell(cell, 'rogue_passage')
			self.strata.set_cell(tunnel.start, 'rogue_door')
			self.strata.set_cell(tunnel.stop, 'rogue_door')

		enter_room_key = self.builder.rng.choice(list(builder.grid.size.iter_points()))
		enter_room = builder.grid.cell(enter_room_key)
		self.start_pos = Point(
					self.builder.rng.range(enter_room.topleft.x + 1, enter_room.topleft.x + enter_room.size.width + 1 - 1),
					self.builder.rng.range(enter_room.topleft.y + 1, enter_room.topleft.y + enter_room.size.height + 1 - 1),
					)

		for _ in range(9):
			exit_room_key = self.builder.rng.choice(list(builder.grid.size.iter_points()))
			exit_room = builder.grid.cell(exit_room_key)
			self.exit_pos = Point(
					self.builder.rng.range(exit_room.topleft.x + 1, exit_room.topleft.x + exit_room.size.width + 1 - 1),
					self.builder.rng.range(exit_room.topleft.y + 1, exit_room.topleft.y + exit_room.size.height + 1 - 1),
					)
			if exit_room_key != enter_room_key:
				break
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

class BSPBuilder(object):
	""" Fills specified field with binary space partition.
	"""
	def __init__(self, field, free=False, obstacle=True, door=False):
		""" Accepts three callables that should return ID of a corresponding terrain:
		- free cell (floor)
		- obstacle (wall)
		- door (or doorway)
		"""
		self.field = field
		self.free, self.obstacle, self.door = free, obstacle, door
	def fill(self, topleft, bottomright, is_horizontal, door_pos):
		""" Uses tuples generated by BinarySpacePartition.
		Draws a line with a 'door', overwrites all cell contents for specified rectangle.
		"""
		for x in range(topleft.x, bottomright.x + 1):
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell((x, y), self.free())
		if is_horizontal:
			the_divide = door_pos.x
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell((the_divide, y), self.obstacle())
		else:
			the_divide = door_pos.y
			for x in range(topleft.x, bottomright.x + 1):
				self.field.set_cell((x, the_divide), self.obstacle())
		self.field.set_cell(door_pos, self.door())

class BSPBuildingBuilder(BSPBuilder):
	""" Like BSPBuilder, but produces solid "buildings" made of "obstacle" terrain
	instead of rooms, and uses "free" terrain to crease "roads" between buildings
	instead of walls.
	"""
	def fill(self, topleft, bottomright, is_horizontal, door_pos):
		""" Uses tuples generated by BinarySpacePartition.
		Generated buildings are 1 cell narrower in every direction
		to give space for roads, which take +1 width in both direction correspondingly, resulting in width of 3 cells.
		"""
		for x in range(topleft.x + 3, bottomright.x + 1 - 3):
			for y in range(topleft.y + 3, bottomright.y + 1 - 3):
				self.field.set_cell((x, y), self.obstacle())
		if is_horizontal:
			the_divide = door_pos.x
			for y in range(topleft.y, bottomright.y + 1):
				self.field.set_cell((the_divide - 1, y), self.free())
				self.field.set_cell((the_divide, y), self.free())
				self.field.set_cell((the_divide + 1, y), self.free())
		else:
			the_divide = door_pos.y
			for x in range(topleft.x, bottomright.x + 1):
				self.field.set_cell((x, the_divide - 1), self.free())
				self.field.set_cell((x, the_divide), self.free())
				self.field.set_cell((x, the_divide + 1), self.free())
		self.field.set_cell(door_pos, self.door())

class BSPDungeon(Builder):
	""" Builds closed set of rooms/galleries/quarters
	packed into large rectangular space.
	"""
	def _build(self):
		Log.debug("Building surrounding walls.")
		for x in range(self.builder.size.width):
			self.strata.set_cell((x, 0), 'wall')
			self.strata.set_cell((x, self.builder.size.height - 1), 'wall')
		for y in range(self.builder.size.height):
			self.strata.set_cell((0, y), 'wall')
			self.strata.set_cell((self.builder.size.width - 1, y), 'wall')

		Log.debug("Running BSP...")
		partition = bsp.BinarySpacePartition(self.builder.rng)
		builder = BSPBuilder(self.strata,
								 free=lambda: 'floor',
								 obstacle=lambda: 'wall',
								 door=lambda: 'floor',
						 )
		for splitter in partition.generate(Point(1, 1), Point(self.builder.size.width - 2, self.builder.size.height - 2)):
			Log.debug("Splitter: {0}".format(splitter))
			builder.fill(*splitter)

		floor_only = lambda pos: self.strata.cell(pos) == 'floor'
		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.start_pos = pcg.TryCheck(pcg.point).check(floor_only)(self.builder.rng, self.builder.size)
		Log.debug("Generated player pos: {0}".format(self.start_pos))

		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.exit_pos = pcg.TryCheck(pcg.point).check(lambda pos: floor_only(pos) and pos != self.start_pos)(self.builder.rng, self.builder.size)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

class CityBuilder(Builder):
	""" A city block of buildings, surrounded by a thick wall.
	"""
	def _build(self):
		Log.debug("Building surrounding walls.")
		for x in range(self.builder.size.width):
			self.strata.set_cell((x, 0), 'wall')
			self.strata.set_cell((x, self.builder.size.height - 1), 'wall')
		for y in range(self.builder.size.height):
			self.strata.set_cell((0, y), 'wall')
			self.strata.set_cell((self.builder.size.width - 1, y), 'wall')
		for x in range(1, self.builder.size.width - 1):
			for y in range(1, self.builder.size.height - 1):
				self.strata.set_cell((x, y), 'floor')

		Log.debug("Running BSP...")
		partition = bsp.BinarySpacePartition(self.builder.rng, min_width=8, min_height=7)
		partition.set_unfit_both_dimensions(True)
		builder = BSPBuildingBuilder(self.strata,
								 free=lambda: 'floor',
								 obstacle=lambda: 'wall',
								 door=lambda: 'floor',
						 )
		for splitter in partition.generate(Point(1, 1), Point(self.builder.size.width - 2, self.builder.size.height - 2)):
			Log.debug("Splitter: {0}".format(splitter))
			builder.fill(*splitter)

		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		floor_only = lambda pos: self.strata.cell(pos) == 'floor'
		self.start_pos = pcg.TryCheck(pcg.point).check(floor_only)(self.builder.rng, self.builder.size)
		Log.debug("Generated player pos: {0}".format(self.start_pos))

		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.exit_pos = pcg.TryCheck(pcg.point).check(lambda pos: floor_only(pos) and pos != self.start_pos)(self.builder.rng, self.builder.size)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

class CaveBuilder(Builder):
	""" A large open natural cave.
	"""
	def _build(self):
		self.strata = clckwrkbdgr.pcg.cellular.cave(self.builder.rng, self.builder.size)

		floor_only = lambda pos: self.strata.cell(pos) > 1
		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.start_pos = pcg.TryCheck(pcg.point).check(floor_only)(self.builder.rng, self.builder.size)
		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.exit_pos = pcg.TryCheck(pcg.point).check(lambda pos: floor_only(pos) and pos != self.start_pos)(self.builder.rng, self.builder.size)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))

		for pos in self.strata.size.iter_points():
			if self.strata.cell(pos):
				self.strata.set_cell(pos, 'floor')
			else:
				self.strata.set_cell(pos, 'wall')

class MazeBuilder(Builder):
	""" A maze labyrinth on a grid.
	Size of the grid cell is controlled by the field CELL_SIZE, default is 1 cell.
	"""
	CELL_SIZE = Size(1, 1)
	def _fill_maze(self, layout, floor_terrain='tunnel_floor'):
		""" Fills actual map with terrain IDs according to given layout
		and considering cell_size.
		"""
		self.strata = Matrix(self.builder.size, 'wall')
		for pos in layout.size.iter_points():
			if layout.cell(pos):
				for x in range(self.CELL_SIZE.width):
					for y in range(self.CELL_SIZE.height):
						self.strata.set_cell((
								1 + pos.x * self.CELL_SIZE.width + x,
								1 + pos.y * self.CELL_SIZE.height + y,
								), floor_terrain,
								)
	def _place_points(self):
		""" Places other points of interests (start, exit).
		"""
		floor_only = lambda pos: self.strata.cell(pos) in ['floor', 'tunnel_floor']
		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.start_pos = pcg.TryCheck(pcg.point).check(floor_only)(self.builder.rng, self.builder.size)
		Log.debug("Generated player pos: {0}".format(self.start_pos))

		pcg.point(self.builder.rng, self.builder.size) # FIXME work around legacy bug which scrapped the first result
		self.exit_pos = pcg.TryCheck(pcg.point).check(lambda pos: floor_only(pos) and pos != self.start_pos)(self.builder.rng, self.builder.size)
		Log.debug("Generated exit pos: {0}".format(self.exit_pos))
	def _build(self):
		maze = clckwrkbdgr.pcg.maze.Maze(self.builder.rng, self.builder.size, self.CELL_SIZE)
		layout = maze.build()
		self._fill_maze(layout)
		self._place_points()

class Sewers(MazeBuilder):
	""" Sewers: labyrinth of wide tunnels with water streams.
	"""
	CELL_SIZE = Size(4, 3)
	def _fill_maze(self, layout):
		""" In addition to carving tunnels
		also pours water in them, making a connected set of streams
		with floor boardwalks under walls.
		"""
		super(Sewers, self)._fill_maze(layout, floor_terrain='floor')

		# Fill water streams.
		for x in range(self.builder.size.width):
			for y in range(self.builder.size.height):
				if self.strata.cell((x, y)) == 'wall':
					continue
				for n in clckwrkbdgr.math.get_neighbours(self.strata, (x, y), with_diagonal=True):
					if self.strata.cell(n) == 'wall':
						break
				else:
					self.strata.set_cell((x, y), 'water')
