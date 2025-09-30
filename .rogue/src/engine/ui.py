import string
import logging
Log = logging.getLogger('rogue')
from collections import namedtuple
from clckwrkbdgr import utils
from clckwrkbdgr.math import Point, Direction, Rect, Size
import clckwrkbdgr.tui
from ._base import Events

DIRECTION = {
		'h' : Direction.LEFT,
		'j' : Direction.DOWN,
		'k' : Direction.UP,
		'l' : Direction.RIGHT,
		'y' : Direction.UP_LEFT,
		'u' : Direction.UP_RIGHT,
		'b' : Direction.DOWN_LEFT,
		'n' : Direction.DOWN_RIGHT,
		}

Sprite = namedtuple('Sprite', 'sprite color')

class Indicator(object):
	""" Status indicator.
	Displays updatable value with optional label at specified location
	and takes fixed width.
	"""
	def __init__(self, width, value_getter):
		""" Value getter should take Mode as parameter
		and return string value of specified width or less.
		Result string will be padded automatically.
		"""
		self.width = width
		self.value_getter = value_getter
	def draw(self, ui, pos, mode):
		value = self.value_getter(mode)
		if value is not None:
			ui.print_line(pos.y, pos.x, value.ljust(self.width))

class CaptionedIndicator(Indicator):
	""" Displays static caption with dynamic value
	if form "caption: value"
	"""
	def __init__(self, caption, value_width, value_getter, sep=": "):
		""" Full width is calculated from caption length and given value width.
		Value getter should return only value.
		If returned value is None, hides indicator completely.
		"""
		super(CaptionedIndicator, self).__init__(len(caption) + len(sep) + value_width, self.get_value)
		self.caption = caption
		self.sep = sep
		self.actual_value_getter = value_getter
	def get_value(self, mode):
		value = self.actual_value_getter(mode)
		return '{0}{1}{2}'.format(self.caption, self.sep, str(value)) if value is not None else ''

_MainKeys = clckwrkbdgr.tui.Keymapping()
class MainGame(clckwrkbdgr.tui.Mode):
	""" Main game mode: map, status line/panel, messages.
	"""
	Keys = _MainKeys
	KEYMAPPING = _MainKeys
	INDICATORS = [] # See .draw_status()

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
	def get_viewport(self): # pragma: no cover
		""" Should return Size of a map view port. """
		raise NotImplementedError()
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
		return self.game.get_sprite(pos, cell_info=cell_info)
	
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
			cursor = self.aim + self.get_map_shift() - self.get_viewrect().topleft
			ui.cursor().move(cursor.x, cursor.y)
	def draw_map(self, ui):
		""" Redraws map according to get_viewrect() and get_sprite().
		"""
		view_rect = self.get_viewrect()
		Log.debug('View rect: {0}'.format(view_rect))
		for world_pos, cell_info in self.game.scene.iter_cells(view_rect):
			sprite = self.get_sprite(world_pos, cell_info)
			if sprite is None:
				continue
			viewport_pos = world_pos - view_rect.topleft
			screen_pos = viewport_pos + self.get_map_shift()
			#Log.debug('World: {0}, view: {1}, screen: {2}'.format(world_pos, viewport_pos, screen_pos))
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
		to_remove, message_line = clckwrkbdgr.text.wrap_lines(self.messages, width=line_width, ellipsis="[...]", rjust_ellipsis=True)
		if not to_remove:
			del self.messages[:]
		elif to_remove > 0:
			self.messages = self.messages[to_remove:]
		else:
			self.messages[0] = self.messages[0][-to_remove:]
		ui.print_line(pos.y, pos.x, message_line.ljust(line_width))
	def draw_status(self, ui):
		""" Draws status line/panel with indicators defined in .INDICATORS,
		which should be a list of tuples (pos, Indicator).
		Pos should be either a point or an integer (line number) - in the
		latter case it will draw on the same line as previous indicator,
		but fit right next to it, considering its width.
		See Indicator for details.
		"""
		prev_pos, prev_width = Point(0, -1), 0
		for pos, indicator in self.INDICATORS:
			if isinstance(pos, int):
				if pos == prev_pos.y:
					pos = Point(prev_pos.x + prev_width + 1, prev_pos.y)
				else:
					pos = Point(0, pos)
			else:
				pos = Point(pos)
			indicator.draw(ui, pos, self)
			prev_pos, prev_width = pos, indicator.width

	# Actual controls.

	@_MainKeys.bind('S')
	def exit_game(self):
		""" Save and quit. """
		Log.debug('Exiting the game.')
		return True
	@_MainKeys.bind('o')
	def start_autoexplore(self):
		""" Autoexplore. """
		self.game.automove()
	@_MainKeys.bind(list('hjklyubn'), lambda key:DIRECTION[str(key)])
	def move_player(self, direction):
		""" Move around. """
		Log.debug('Moving.')
		if self.aim:
			new_pos = self.aim + direction
			if self.game.scene.valid(new_pos) and self.get_viewrect().contains(new_pos, with_border=True):
				self.aim = new_pos
		else:
			self.game.move_actor(self.game.scene.get_player(), direction)
	@_MainKeys.bind('.')
	def wait(self):
		""" Wait in-place / go to selected aim. """
		if self.aim:
			self.game.automove(self.aim)
			self.aim = None
		else:
			self.game.wait(self.game.scene.get_player())
	@_MainKeys.bind('g')
	def grab_item(self):
		""" Grab item. """
		self.game.grab_item_here(self.game.scene.get_player())
	@_MainKeys.bind('?')
	def help(self):
		""" Show this help. """
		return HelpScreen()
	@_MainKeys.bind('Q')
	def suicide(self):
		""" Suicide (quit without saving). """
		Log.debug('Suicide.')
		self.game.suicide(self.game.scene.get_player())
	@_MainKeys.bind('x')
	def examine(self):
		""" Examine surroundings (cursor mode). """
		if self.aim:
			self.aim = None
		else:
			self.aim = self.game.scene.get_global_pos(self.game.scene.get_player())
	@_MainKeys.bind('>')
	def descend(self):
		""" Descend/go down. """
		if not self.aim:
			self.game.descend(self.game.scene.get_player())
	@_MainKeys.bind('<')
	def ascend(self):
		""" Ascend/go up. """
		if not self.aim:
			self.game.ascend(self.game.scene.get_player())
	@_MainKeys.bind('~')
	def god_mode(self):
		""" God mode options. """
		return GodModeMenu(self.game)
	@_MainKeys.bind('i')
	def show_inventory(self):
		""" Show inventory. """
		return Inventory(self.game.scene.get_player())
	@_MainKeys.bind('d')
	def drop_item(self):
		""" Drop item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		return Inventory(
				self.game.scene.get_player(),
				caption = "Select item to drop:",
				on_select = self.game.drop_item
			)
	@_MainKeys.bind('e')
	def consume(self):
		""" Consume item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		return Inventory(
				self.game.scene.get_player(),
				caption = "Select item to consume:",
				on_select = self.game.consume_item,
				)
	@_MainKeys.bind('w')
	def wield(self):
		""" Wield item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		return Inventory(
				self.game.scene.get_player(),
				caption = "Select item to wield:",
				on_select = self.game.wield_item,
				)
	@_MainKeys.bind('U')
	def unwield(self):
		""" Unwield item. """
		self.game.unwield_item(self.game.scene.get_player())
	@_MainKeys.bind('W')
	def wear(self):
		""" Wear item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		return Inventory(
				self.game.scene.get_player(),
				caption = "Select item to wear:",
				on_select = self.game.wear_item,
				)
	@_MainKeys.bind('T')
	def take_off(self):
		""" Take item off. """
		self.game.take_off_item(self.game.scene.get_player())
	@_MainKeys.bind('E')
	def show_equipment(self):
		""" Show equipment. """
		return Equipment(self.game, self.game.scene.get_player())
	@_MainKeys.bind('q')
	def show_questlog(self):
		""" List current quests. """
		return QuestLog(self.game.scene, list(self.game.scene.iter_active_quests()))
	@_MainKeys.bind('C')
	def chat(self):
		""" Chat with NPC. """
		npcs = self.game.get_respondents(self.game.scene.get_player())
		if not npcs:
			return None
		def _chat_with_npc(npc):
			prompt, on_yes, on_no = self.game.chat(self.game.scene.get_player(), npc)
			if prompt:
				return TradeDialogMode('"{0}" (y/n)'.format(prompt),
							on_yes=on_yes, on_no=on_no)
		if len(npcs) > 1:
			return DirectionDialogMode(on_direction=_chat_with_npc)
		return _chat_with_npc(npcs[0])
	@_MainKeys.bind('M')
	def show_map(self):
		""" Show map. """
		return MapScreen(self.game.scene, self.get_viewport())
	@_MainKeys.bind('O')
	def open_close_doors(self):
		""" Open/close nearby doors. """
		self.game.toggle_nearby_doors(self.game.scene.get_player())

class MapScreen(clckwrkbdgr.tui.Mode):
	""" Map of the surrounding area (if Scene allows). """
	def __init__(self, scene, size):
		self.scene = scene
		self.size = size
	def redraw(self, ui):
		area_map = self.scene.make_map(self.size)
		if not area_map:
			ui.print_line(0, 0, 'No map for current location.')
			ui.print_line(1, 0, '[Press Any Key...]')
			return
		for pos in area_map:
			sprite = area_map.cell(pos)
			if not sprite:
				continue
			ui.print_char(pos.x, pos.y, sprite.sprite, sprite.color)
		ui.print_line(area_map.height, 0, '[Press Any Key...]')
	def action(self, control):
		return False

class HelpScreen(clckwrkbdgr.tui.Mode):
	""" Main help screen with controls cheatsheet. """
	def redraw(self, ui):
		for row, (_, binding) in enumerate(MainGame.Keys.list_all()):
			if utils.is_collection(binding.key):
				keys = ''.join(map(str, binding.key))
			else:
				keys = str(binding.key)
			ui.print_line(row, 0, '{0} - {1}'.format(keys, binding.help))
		ui.print_line(row + 1, 0, '[Press Any Key...]')
	def action(self, control):
		return False

GodModeKeys = clckwrkbdgr.tui.Keymapping()
class GodModeMenu(clckwrkbdgr.tui.Mode):
	""" God mode options. """
	KEYMAPPING = GodModeKeys
	def __init__(self, game):
		self.game = game
		self.getters = {
			'v': lambda: self.game.god.vision,
			'c': lambda: self.game.god.noclip,
			}
	def redraw(self, ui):
		ui.print_line(0, 0, 'Select God option:')
		for row, (_, binding) in enumerate(self.KEYMAPPING.list_all()):
			ui.print_line(1 + row, 0, '{0} - [{1}] - {2}'.format(
				binding.key, 'X' if self.getters[binding.key]() else ' ',
				binding.help
				))
	def action(self, control):
		return False
	@GodModeKeys.bind('v')
	def vision(self):
		""" See all. """
		self.game.god.toggle_vision()
		self.game.fire_event(Events.GodModeSwitched('vision', self.game.god.vision))
	@GodModeKeys.bind('c')
	def noclip(self):
		""" Walk through walls. """
		self.game.god.toggle_noclip()
		self.game.fire_event(Events.GodModeSwitched('noclip', self.game.god.noclip))

InventoryKeys = clckwrkbdgr.tui.Keymapping()
class Inventory(clckwrkbdgr.tui.Mode):
	""" Inventory menu.
	Supports prompting message.
	"""
	TRANSPARENT = False
	KEYMAPPING = InventoryKeys
	def __init__(self, actor, caption=None, on_select=None):
		""" Shows actor's inventory with optional prompt
		and callable action upon selecting an item.
		By default pressing any key will close the inventory view.
		Selector should accept params: (actor, item).
		"""
		self.actor = actor
		self.inventory = actor.inventory
		self.prompt = caption or "Inventory:"
		self.on_select = on_select
	def redraw(self, ui):
		if self.prompt:
			ui.print_line(0, 0, self.prompt)
		if not self.inventory:
			ui.print_line(1, 0, '(Empty)')
			return
		accumulated = []
		for shortcut, item in zip(string.ascii_lowercase, self.inventory):
			for other in accumulated:
				if other[1].name == item.name:
					other[2] += 1
					break
			else:
				accumulated.append([shortcut, item, 1])
		for index, (shortcut, item, amount) in enumerate(accumulated):
			column = index // 20
			index = index % 20
			ui.print_line(index + 1, column * 40 + 0, '[{0}] '.format(shortcut))
			ui.print_line(index + 1, column * 40 + 4, item.sprite.sprite, item.sprite.color)
			if amount > 1:
				ui.print_line(index + 1, column * 40 + 6, '- {0} (x{1})'.format(item.name, amount))
			else:
				ui.print_line(index + 1, column * 40 + 6, '- {0}'.format(item.name))
	def action(self, done):
		return not done
	@InventoryKeys.bind(list(string.ascii_lowercase), param=lambda key:str(key))
	def select(self, param):
		""" Select item and close inventory. """
		if not self.on_select:
			return True
		index = ord(param) - ord('a')
		if index >= len(self.inventory):
			self.prompt = "No such item ({0})".format(param)
			return None
		if not self.on_select(self.actor, self.inventory[index]):
			return False
		return True
	@InventoryKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self):
		""" Close by Escape. """
		return True

EquipmentKeys = clckwrkbdgr.tui.Keymapping()
class Equipment(clckwrkbdgr.tui.Mode):
	""" Equipment menu.
	"""
	KEYMAPPING = EquipmentKeys
	def __init__(self, game, actor):
		self.game = game
		self.actor = actor
		self.done = False
	def redraw(self, ui):
		wielding = self.actor.wielding
		if wielding:
			wielding = wielding.name
		wearing = self.actor.wearing
		if wearing:
			wearing = wearing.name
		ui.print_line(0, 0, 'wielding [a] - {0}'.format(wielding))
		ui.print_line(1, 0, 'wearing  [b] - {0}'.format(wearing))
	def action(self, done):
		return not (done or self.done)
	@EquipmentKeys.bind('a')
	def wield(self):
		""" Wield or unwield item. """
		if self.actor.wielding:
			self.game.unwield_item(self.actor)
			return True
		self.done = True
		return Inventory(
				self.actor,
				caption = "Select item to wield:",
				on_select = self.game.wield_item,
				)
	@EquipmentKeys.bind('b')
	def wear(self):
		""" Wear or take off item. """
		if self.actor.wearing:
			self.game.take_off_item(self.actor)
			return True
		self.done = True
		return Inventory(
				self.actor,
				caption = "Select item to wear:",
				on_select = self.game.wear_item,
				)
	@EquipmentKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self):
		""" Close by Escape. """
		return True

DirectionKeys = clckwrkbdgr.tui.Keymapping()
class DirectionDialogMode(clckwrkbdgr.tui.Mode):
	""" User prompt to pick direction in case where there are
	multiple options for some action.
	"""
	TRANSPARENT = True
	KEYMAPPING = DirectionKeys
	def __init__(self, on_direction=None):
		self.on_direction = on_direction
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, "Too crowded. Chat in which direction?")
	@DirectionKeys.bind(list(DIRECTION.keys()), lambda key:DIRECTION[str(key)])
	def choose_direction(self, direction):
		return self.on_direction(direction) if self.on_direction else False
	def action(self, control):
		return False

DialogKeys = clckwrkbdgr.tui.Keymapping()
DialogKeys.map(list('yY'), True)
class TradeDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DialogKeys
	def __init__(self, question, on_yes=None, on_no=None):
		self.question = question
		self.on_yes = on_yes
		self.on_no = on_no
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, self.question)
	def action(self, control):
		if control:
			if self.on_yes:
				self.on_yes()
		else:
			if self.on_no:
				self.on_no()

QuestLogKeys = clckwrkbdgr.tui.Keymapping()
class QuestLog(clckwrkbdgr.tui.Mode):
	TRANSPARENT = False
	KEYMAPPING = QuestLogKeys
	def __init__(self, scene, quests):
		self.scene = scene
		self.quests = quests
	def redraw(self, ui):
		if not self.quests:
			ui.print_line(0, 0, "No current quests.")
		else:
			ui.print_line(0, 0, "Current quests:")
		for index, (npc, quest) in enumerate(self.quests):
			ui.print_line(index + 1, 0, npc.name)
			ui.print_line(index + 1, len(npc.name) + 1, npc.sprite.sprite, npc.sprite.color)
			ui.print_line(index + 1, len(npc.name) + 3, "{0}: {1}".format(
				self.scene.get_str_location(npc), quest.summary(),
				))
	def action(self, done):
		return not done
	@QuestLogKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self):
		""" Close by Escape. """
		return True
