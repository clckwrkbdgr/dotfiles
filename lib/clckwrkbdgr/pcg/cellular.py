import logging
Log = logging.getLogger(__name__)
from ..math import Point, Matrix
from ..math.grid import get_neighbours
"""
Map generation using cellular automatas.
"""

NEIGHS = [
		(-1, -1), (-1, 0), (-1, 1),
		( 0, -1),          ( 0, 1),
		(+1, -1), (+1, 0), (+1, 1),
		]
NEIGHS_2 = [
		(-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
		(-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2),
		( 0, -2), ( 0, -1), ( 0, 0),  ( 0, 1), ( 0, 2),
		(+1, -2), (+1, -1), (+1, 0), (+1, 1), (+1, 2),
		(+2, -2), (+2, -1), (+2, 0), (+2, 1), (+2, 2),
		]

def cave(rng, size):
	""" Generates Matrix with cave-like structure.
	All caverns are connected.
	Returns Matrix of integer cells: zero means "wall", non-zero - empty space.
	"""
	grid = Matrix(size, 0)
	for x in range(1, grid.size.width - 1):
		for y in range(1, grid.size.height - 1):
			grid.set_cell((x, y), 0 if rng.get() < 0.50 else 1)
	Log.debug("Initial state:\n{0}".format(repr(grid)))

	new_layer = Matrix(grid.size)
	drop_wall_2_at = 4
	for step in range(drop_wall_2_at+1):
		for x in range(1, grid.size.width - 1):
			for y in range(1, grid.size.height - 1):
				wall_count = 0
				for n in NEIGHS:
					if grid.cell((x + n[0], y + n[1])) == 0:
						wall_count += 1
						if wall_count >= 5:
							break
				if wall_count >= 5:
					new_layer.set_cell((x, y), 0)
					continue
				if step < drop_wall_2_at:
					wall_2_count = 0
					for n in NEIGHS_2:
						n = Point(x + n[0], y + n[1])
						if not grid.valid(n):
							continue
						if grid.cell(n) == 0:
							wall_2_count += 1
							if wall_2_count > 2:
								break
					if wall_2_count <= 2:
						new_layer.set_cell((x, y), 0)
						continue
				new_layer.set_cell((x, y), 1)
		grid, new_layer = new_layer, grid
		Log.debug("Step {1}:\n{0}".format(repr(grid), step))
	
	cavern = next(pos for pos in grid.size.iter_points() if grid.cell(pos) == 1)
	caverns = []
	while cavern:
		area = []
		already_affected = {cavern}
		last_wave = {cavern}
		area.append(cavern)
		while last_wave:
			Log.debug('Last wave: {0}'.format(len(last_wave)))
			wave = set()
			for point in last_wave:
				wave |= {x for x in get_neighbours(grid, point) if grid.cell(x) == 1}
			for point in wave - already_affected:
				area.append(point)
			last_wave = wave - already_affected
			already_affected |= wave

		count = 0
		for point in area:
			count += 1
			grid.set_cell(point, 2 + len(caverns))
		caverns.append(count)
		Log.debug("Filling cavern #{1}:\n{0}".format(repr(grid), len(caverns)))
		cavern = next((pos for pos in grid.size.iter_points() if grid.cell(pos) == 1), None)
	max_cavern = 2 + caverns.index(max(caverns))
	for pos in grid.size.iter_points():
		if grid.cell(pos) in [0, max_cavern]:
			continue
		grid.set_cell(pos, 0)
	Log.debug("Finalized cave:\n{0}".format(repr(grid)))
	return grid
