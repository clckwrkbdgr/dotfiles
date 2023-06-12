import sys
import random
import curses
import logging
trace = logging.getLogger('rogue')
from .. import logging
from ..fs import SerializedEntity
from .. import xdg
from ..math import algorithm
from ..math import Point, Size, Rect, get_neighbours, sign
from .dungeon import Dungeon

def main(stdscr):
	logging.init('rogue',
			debug='-d' in sys.argv,
			filename=xdg.save_state_path('dotrogue')/'rogue.log',
			stream=None,
			)
	curses.curs_set(0)
	savefile = SerializedEntity(xdg.save_data_path('dotrogue')/'rogue.sav', 0, entity_name='dungeon', unlink=False, readable=True)
	savefile.load()
	if savefile.entity:
		dungeon = savefile.entity
	else:
		dungeon = Dungeon()
		savefile.reset(dungeon)
	game = Game(dungeon)
	game.run(stdscr)
	savefile.save()

class DungeonWave(algorithm.Wave):
	def __init__(self, matrix, region):
		self.matrix = matrix
		self.region = region
	def is_linked(self, node_from, node_to):
		distance = abs(node_from - node_to)
		return distance.x <= 1 and distance.y <= 1
	def get_links(self, node):
		return [p for p in get_neighbours(
			self.matrix, node,
			with_diagonal=True,
			check=lambda c: c == '.'
			)
			 if self.region.contains(p, with_border=True)
			 ]

class Autoexplorer:
	def __init__(self):
		self.path = None
		self.previous_direction = None
	def process(self, dungeon):
		if self.path:
			direction = self.path.pop(0)
			self.previous_direction = direction
			return direction
		target = dungeon.rogue
		for _ in range(100):
			target = Point(
					random.randrange(dungeon.rogue.x - 10, dungeon.rogue.x + 10),
					random.randrange(dungeon.rogue.y - 10, dungeon.rogue.y + 10),
					)
			trace.debug('Autoexplorer target: trying {0}'.format(target))
			if dungeon.terrain.cell(target) != '.':
				trace.debug('Autoexplorer target: {0}: not passable'.format(target))
				continue
			distance = target - dungeon.rogue
			diff = abs(distance)
			direction = Point(sign(distance.x), sign(distance.y))
			trace.debug('Autoexplorer target: selected direction: {0}'.format(direction))
			if self.previous_direction:
				trace.debug('Autoexplorer target: previous direction: {0}'.format(self.previous_direction))
				if self.previous_direction.x == 0:
					old_directions = [
							Point(-1, 0),
							Point(-1, -self.previous_direction.y),
							Point(0, -self.previous_direction.y),
							Point(1, -self.previous_direction.y),
							Point(1, 0),
							]
				elif self.previous_direction.y == 0:
					old_directions = [
							Point(0, -1),
							Point(-self.previous_direction.x, -1),
							Point(-self.previous_direction.x, 0),
							Point(-self.previous_direction.x, 1),
							Point(0, 1),
							]
				else:
					old_directions = [
							Point(self.previous_direction.x, -self.previous_direction.y),
							Point(0, -self.previous_direction.y),
							Point(-self.previous_direction.x, -self.previous_direction.y),
							Point(-self.previous_direction.x, 0),
							Point(-self.previous_direction.x, self.previous_direction.y),
							]
				trace.debug('Autoexplorer target: old direction fan: {0}'.format(old_directions))
				if direction in old_directions:
					trace.debug('Autoexplorer target: selected direction is old.')
					continue
			if not(3 < diff.x < 10 and 3 < diff.y < 10):
				trace.debug('Autoexplorer target: too close or too far: {0}'.format(target))
				continue
			trace.debug('Autoexplorer target: good, picking {0}'.format(target))
			break
		wave = DungeonWave(dungeon.terrain, Rect(
			topleft=dungeon.rogue - Point(10, 10),
			size=Size(21, 21),
			))
		trace.debug('Autoexplorer forming path: {0} -> {1}'.format(dungeon.rogue, target))
		path = wave.run(dungeon.rogue, target)
		trace.debug('Autoexplorer wave: {0}'.format(path))
		self.path = list(b - a for a, b in zip(path, path[1:]))
		trace.debug('Autoexplorer sequence: {0}'.format(self.path))
		return self.process(None)

class Game:
	CONTROLS = {(ord(k) if isinstance(k, str) else k):v for k,v in {
		'q' : SystemExit,
		'o' : 'autoexplore',
		'h' : Point(-1,  0),
		'j' : Point( 0, +1),
		'k' : Point( 0, -1),
		'l' : Point(+1,  0),
		'y' : Point(-1, -1),
		'u' : Point(+1, -1),
		'b' : Point(-1, +1),
		'n' : Point(+1, +1),

		-1 : 'autoexplore',
		27 : 'ESC',
		}.items()}
	VIEW_CENTER = Point(12, 12)

	def __init__(self, dungeon):
		self.dungeon = dungeon
		self.autoexplore = None
	def run(self, stdscr):
		while True:
			self.view(stdscr)
			if not self.control(stdscr):
				break
	def view(self, stdscr):
		for y in range(-self.VIEW_CENTER.y, 25 - self.VIEW_CENTER.y):
			for x in range(-self.VIEW_CENTER.x, 25 - self.VIEW_CENTER.x):
				stdscr.addstr(self.VIEW_CENTER.y + y, self.VIEW_CENTER.x + x, self.dungeon.get_sprite((x, y)))
		stdscr.addstr(0, 27, 'Time: {0}'.format(self.dungeon.time))
		stdscr.addstr(1, 27, 'X:{x} Y:{y}  '.format(x=self.dungeon.rogue.x, y=self.dungeon.rogue.y))
		stdscr.addstr(24, 27, '[autoexploring, press ESC...]' if self.autoexplore else '                             ')
		stdscr.refresh()
	def control(self, stdscr):
		char = stdscr.getch()
		control = self.CONTROLS.get(char)
		trace.debug('Curses char: {0}'.format(repr(char)))
		trace.debug('Control: {0}'.format(repr(control)))
		trace.debug('Autoexplore={0}'.format(self.autoexplore))
		if control is None:
			return True
		if control == 'autoexplore':
			if self.autoexplore:
				control = self.autoexplore.process(self.dungeon)
				trace.debug('Autoexploring: {0}'.format(repr(control)))
			else:
				trace.debug('Starting self.autoexplore.')
				self.autoexplore = Autoexplorer()
				stdscr.nodelay(1)
				stdscr.timeout(100)
				return True
		elif control == 'ESC':
			trace.debug('Stopping self.autoexplore.')
			self.autoexplore = None
			stdscr.timeout(-1)
			stdscr.nodelay(0)
			return True
		try:
			self.dungeon.control(control)
		except SystemExit:
			trace.debug('Exiting...')
			return False
		return True

if __name__ == '__main__':
	curses.wrapper(main)
