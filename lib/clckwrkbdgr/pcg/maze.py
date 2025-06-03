import logging
Log = logging.getLogger(__name__)
from ..math import Point, Size, Matrix
"""
Generation of mazes/labyrinths.
"""

class Maze:
	""" A simple maze that fill rectangular space.
	"""
	def __init__(self, rng, size, cell_size=None):
		""" Size of the grid cell (walls, passages) is controlled by the cell_size, default is 1x1 cell.
		"""
		self.rng = rng
		self.size = size
		self.cell_size = cell_size or Size(1, 1)
	def _RandomDirections(self):
		""" Changes the direction to go from the current square, to the next available.
		"""
		direction = self.rng.range(4)
		if direction == 0:
			cDir = [Point(-1, 0), Point(1, 0), Point(0, -1), Point(0, 1)]
		elif direction == 1:
			cDir = [Point(0, 1), Point(0, -1), Point(1, 0), Point(-1, 0)]
		elif direction == 2:
			cDir = [Point(0, -1), Point(0, 1), Point(-1, 0), Point(1, 0)]
		elif direction == 3:
			cDir = [Point(1, 0), Point(-1, 0), Point(0, 1), Point(0, -1)]
		return cDir
	def build(self):
		""" Plans layout for the maze.
		Returns matrix of boolean cells: True for empty space, False for walls.
		Note: outer walls are note included.
		"""
		layout_size = Size(
				# Layout size should be odd (for connections between cells).
				(self.size.width - 2 - (1 - self.size.width % 2)) // self.cell_size.width,
				(self.size.height - 2 - (1 - self.size.height % 2)) // self.cell_size.height,
				) # For walls.
		layout = Matrix(layout_size, False)

		# 0 is the most random, randomisation gets lower after that
		# less randomisation means more straight corridors
		RANDOMISATION = 0

		intDone = 0
		while intDone + 1 < ((layout_size.width + 1) * (layout_size.height + 1)) / 4:
			expected = ((layout_size.width + 1) * (layout_size.height + 1)) / 4
			# Search only for cells that have potential option to expand.
			potential_exits = 0
			while not potential_exits:
				# this code is used to make sure the numbers are odd
				current = Point(
					self.rng.range(((layout_size.width + 1) // 2)) * 2,
					self.rng.range(((layout_size.height + 1) // 2)) * 2,
					)
				Log.debug((current, layout_size))
				if current.x > 1 and not layout.cell((current.x - 2, current.y)):
					potential_exits += 1
				if current.y > 1 and not layout.cell((current.x, current.y - 2)):
					potential_exits += 1
				if current.x <= layout_size.width - 2 and not layout.cell((current.x + 2, current.y)):
					potential_exits += 1
				if current.y <= layout_size.height - 2 and not layout.cell((current.x, current.y + 2)):
					potential_exits += 1
			# first one is free!
			if intDone == 0:
				layout.set_cell(current, True)
			if not layout.cell(current):
				continue
			layout.set_cell(current, 123)
			layout.set_cell(current, True)
			# always randomisation directions to start
			cDir = self._RandomDirections()
			blnBlocked = False
			while not blnBlocked:
				# only randomisation directions, based on the constant
				if RANDOMISATION == 0 or self.rng.range(RANDOMISATION) == 0:
					cDir = self._RandomDirections()
				blnBlocked = True
				# loop through order of directions
				for intDir in range(4):
					# work out where this direction is
					new_cell = Point(
							current.x + (cDir[intDir].x * 2),
							current.y + (cDir[intDir].y * 2),
							)
					# check if the tile can be used
					if not layout.valid(new_cell) or layout.cell(new_cell):
						continue
					# create a path
					layout.set_cell(new_cell, True)
					# and the square inbetween
					layout.set_cell((current.x + cDir[intDir].x, current.y + cDir[intDir].y), True)
					# this is now the current square
					current = new_cell
					blnBlocked = False
					# increment paths created
					intDone = intDone + 1
					break
		Log.debug("Done {0}/{1} cells:\n{2}".format(intDone, expected, layout.tostring(lambda c:'.' if c else '#')))
		return layout
