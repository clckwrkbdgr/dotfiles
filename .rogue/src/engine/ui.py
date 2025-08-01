from collections import namedtuple
from clckwrkbdgr.math import Point, Rect, Size
import clckwrkbdgr.tui

Sprite = namedtuple('Sprite', 'sprite color')

class Indicator(object):
	""" Status indicator.
	Displays updatable value with optional label at specified location
	and takes fixed width.
	"""
	def __init__(self, pos, width, value_getter):
		""" Value getter should take Mode as parameter
		and return string value of specified width or less.
		Result string will be padded automatically.
		"""
		self.pos = Point(pos)
		self.width = width
		self.value_getter = value_getter
	def draw(self, ui, mode):
		value = self.value_getter(mode)
		ui.print_line(self.pos.y, self.pos.x, value.ljust(self.width))

class MainGame(clckwrkbdgr.tui.Mode):
	""" Main game mode: map, status line/panel, messages.
	"""
	INDICATORS = []

	def __init__(self, game):
		self.game = game
		self.messages = []
		self.aim = None

	# Overridden behavior.

	def nodelay(self):
		return self.game.in_automovement()
	def get_keymapping(self):
		if self.messages:
			return None
		player = self.game.scene.get_player()
		if not (player and player.is_alive()):
			return None
		if self.nodelay():
			return None
		return super(MainGame, self).get_keymapping()
	def pre_action(self):
		if not self.game.scene.get_player():
			return False
		self.game.perform_automovement()
		return True
	def action(self, control):
		if isinstance(control, clckwrkbdgr.tui.Key):
			if self.messages:
				return True
			player = self.game.scene.get_player()
			if not (player and player.is_alive()):
				return False
			self.game.stop_automovement()
			return True
		self.game.process_others()
		return not control

	# Options for customizations.

	def get_map_shift(self): # pragma: no cover
		""" Shift of the topleft point of the map viewport
		from the topleft point of the screen.
		By default map display starts at the (0;0).
		Map viewport size will always be taken from get_viewrect().size
		"""
		return Point(0, 0)
	def get_message_line_rect(self): # pragma: no cover
		""" Rect: shift of the topleft point of the message line
		from the topleft point of the screen,
		and width of the line (height is ignored).
		By default starts at the (0;0) and width is 80.
		"""
		return Rect(Point(0, 0), Size(80, 1))
	def get_viewrect(self): # pragma: no cover
		""" Should return Rect (in world coordinates)
		that defines what part of the current map is to be displayed
		in the main viewport.
		See Scene.iter_cells()
		"""
		raise NotImplementedError()
	def get_sprite(self, pos, cell_info=None):
		""" Returns topmost Sprite object to display at the specified world pos.
		Additional cell info may be passed (see Scene.get_cell_info()).
		"""
		if cell_info is None:
			cell_info = self.game.scene.get_cell_info(pos)
		cell, objects, items, monsters = cell_info
		if self.game.is_visible(pos):
			if monsters:
				return monsters[-1].sprite
			elif items:
				return items[-1].sprite
			elif objects:
				return objects[-1].sprite
			elif cell:
				return cell.sprite
		if self.game.is_visited(pos):
			if objects:
				return objects[-1].sprite
			elif cell and cell.remembered:
				return cell.remembered
		return None
	
	# Displaying.

	def redraw(self, ui):
		""" Redraws all parts of UI: map, message line, status line/panel.
		Also displays cursor if aim mode is enabled.
		"""
		ui.cursor(bool(self.aim))
		self.draw_map(ui)
		self.print_messages(ui, self.get_message_line_rect().topleft, line_width=self.get_message_line_rect().width)
		self.draw_status(ui)
		if self.aim:
			cursor = self.aim + self.get_map_shift()
			ui.cursor().move(cursor.x, cursor.y)
	def draw_map(self, ui):
		""" Redraws map according to get_viewrect() and get_sprite().
		"""
		view_rect = self.get_viewrect()
		for world_pos, cell_info in self.game.scene.iter_cells(view_rect):
			sprite = self.get_sprite(world_pos, cell_info)
			if sprite is None:
				continue
			viewport_pos = world_pos - view_rect.topleft
			screen_pos = viewport_pos + self.get_map_shift()
			ui.print_char(screen_pos.x, screen_pos.y, sprite.sprite, sprite.color)
	def print_messages(self, ui, pos, line_width=80):
		""" Processes unprocessed events and prints
		currently collected messages on line at specified pos
		with specified max. width.
		Clears line if there are no current messages.
		"""
		for result in self.game.process_events(bind_self=self): # pragma: no cover -- TODO
			if not result:
				continue
			self.messages.append(result)

		if not self.messages:
			ui.print_line(pos.y, pos.x, " " * line_width)
			return
		to_remove, message_line = clckwrkbdgr.text.wrap_lines(self.messages, width=line_width)
		if not to_remove:
			del self.messages[:]
		elif to_remove > 0:
			self.messages = self.messages[to_remove:]
		else:
			self.messages[0] = self.messages[0][-to_remove:]
		ui.print_line(pos.y, pos.x, message_line.ljust(line_width))
	def draw_status(self, ui):
		""" Draws status line/panel with indicators defined in .INDICATORS.
		See Indicator for details.
		"""
		for indicator in self.INDICATORS:
			indicator.draw(ui, self)
