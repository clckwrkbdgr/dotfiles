import sys
import contextlib, functools
import time, threading
import tkinter
import string
import configparser
import logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Size, Rect
from clckwrkbdgr.math.grid import Matrix
from clckwrkbdgr.tui import Key, Mode, Keymapping
from clckwrkbdgr import xdg
import clckwrkbdgr.text
import src.engine.ui
from src.engine import Events
from hud import HUD

class Cursor(object): # pragma: no cover -- TODO
	def __init__(self, engine):
		self._pos = Point(0, 0)
		self.engine = engine
	def move(self, x, y):
		self._pos = Point(x, y)

class TkUI(object):
	BACKGROUND = '#222222'
	FOREGROUND = '#aaaaaa'
	CONFIG_FILE = xdg.save_state_path('dotrogue')/'tkui.cfg'
	def __init__(self): # pragma: no cover -- TODO
		self.root = None
		self.view = None
		self._destroying = False
		self.window = Matrix((100, 30), ' ')
		self._cursor = None
		self._font_size = 8
		self._gui_size = 8
		self._buttons = []
	def __enter__(self): # pragma: no cover -- TODO
		if self.CONFIG_FILE.exists():
			config = configparser.ConfigParser()
			config.read(str(self.CONFIG_FILE))
			if config.has_section('font'):
				self._font_size = int(config.get('font', 'size'))
			if config.has_section('gui'):
				self._gui_size = int(config.get('gui', 'size'))

		self.root = tkinter.Tk()
		self.root.config(background=TkUI.BACKGROUND)
		self.root.attributes('-zoomed', True)

		outer_frame = tkinter.Frame(self.root)
		outer_frame.pack(fill='both', expand=True)
		canvas = tkinter.Canvas(outer_frame)
		canvas.pack(side="left", fill="both", expand=True)
		v_scrollbar = tkinter.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
		v_scrollbar.pack(side="right", fill="y")
		h_scrollbar = tkinter.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
		h_scrollbar.pack(side="bottom", fill="x")
		canvas.configure(yscrollcommand=v_scrollbar.set)
		canvas.configure(xscrollcommand=h_scrollbar.set)
		canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion = canvas.bbox("all")))
		inner_frame = tkinter.Frame(canvas)
		inner_frame.config(background=TkUI.BACKGROUND)
		canvas.create_window((0, 0), window=inner_frame, anchor="nw")
		canvas.config(background=TkUI.BACKGROUND)

		menu_frame = tkinter.Frame(inner_frame)
		menu_frame.pack()
		menu_frame.config(background=TkUI.BACKGROUND)
		self._button(menu_frame, text='Exit', command=self.force_exit)
		self._button(menu_frame, text='Font+', command=self.font_bigger)
		self._button(menu_frame, text='Font-', command=self.font_smaller)
		self._button(menu_frame, text='GUI+', command=self.gui_bigger)
		self._button(menu_frame, text='GUI-', command=self.gui_smaller)

		self.mode_frame = tkinter.Frame(inner_frame)
		self.mode_frame.pack()
		self.mode_frame.config(background=TkUI.BACKGROUND)

		self.main_frame = tkinter.Frame(self.mode_frame)
		self.main_frame.pack()
		self.main_frame.config(background=TkUI.BACKGROUND)
		self.view = tkinter.Label(
				self.main_frame,
				text=self.window.tostring(),
				font=("Courier", self._font_size),
				)
		self.view.pack()
		self.view.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

		keys = [
				chr(27) + 'S~gdieOayku',
				' vxwUWTEfh.l',
				'QcqCMo><mbjn',
				'prstz ',
				]
		for keyline in keys:
			frame = tkinter.Frame(self.main_frame)
			frame.pack()
			for key in keyline:
				self._button(frame, text=key, command=lambda _key=key:self._loop.action(Key(ord(_key))))

		for button in self._buttons:
			button.config(font=("Courier", self._gui_size))
		return self
	def __exit__(self, *_targs): # pragma: no cover -- TODO
		config = configparser.ConfigParser()
		with self.CONFIG_FILE.open('w') as f:
			config.add_section('font')
			config.set('font', 'size', str(self._font_size))
			config.add_section('gui')
			config.set('gui', 'size', str(self._gui_size))
			config.write(f)

	def _button(self, frame, text=None, command=None):
		button = tkinter.Button(frame, text=text, command=command)
		button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
		self._buttons.append(button)
		button.pack(side='left')
	def force_exit(self):
		self._destroying = True
		self._loop.mode = None
		self.root.destroy()
	def font_smaller(self):
		self._font_size = max(1, self._font_size - 1)
		self.view.config(font=("Courier", self._font_size))
	def font_bigger(self):
		self._font_size = min(72, self._font_size + 1)
		self.view.config(font=("Courier", self._font_size))
	def gui_smaller(self):
		self._gui_size = max(1, self._gui_size - 1)
		for button in self._buttons:
			button.config(font=("Courier", self._gui_size))
	def gui_bigger(self):
		self._gui_size = min(72, self._gui_size + 1)
		for button in self._buttons:
			button.config(font=("Courier", self._gui_size))

	@contextlib.contextmanager
	def redraw(self, clean=False): # pragma: no cover -- TODO
		try:
			if clean:
				self.window.clear(' ')
			yield self
		finally:
			if self._cursor:
				self.window.set_cell(self._cursor._pos, 'X')
			self.view.config(text=self.window.tostring())
	def print_line(self, row, col, line, color=None): # pragma: no cover -- TODO
		for i in range(len(line)):
			self.window.set_cell((col + i, row), line[i])

	def cursor(self, on=True): # pragma: no cover -- TODO
		""" Switches cursor on/off and returns Cursor object, if on.
		"""
		if on:
			if self._cursor is None:
				self._cursor = Cursor(self)
			return self._cursor
		if self._cursor is not None:
			self._cursor = None
		return None

_MainKeys = Keymapping()
class MainGame(Mode):
	""" Main game mode: map, status line/panel, messages.
	"""
	Keys = _MainKeys
	KEYMAPPING = _MainKeys
	INDICATORS = [
			((62, 0), HUD.Depth),
			((62, 1), HUD.Pos),
			((62, 2), HUD.Time),
			((62, 3), HUD.Here),

			((62, 5), HUD.HP),
			((62, 6), HUD.Inventory),
			((62, 7), HUD.Wield),
			((62, 8), HUD.Wear),

			((62, 22), HUD.GodVision),
			((67, 22), HUD.GodNoclip),

			((62, 23), HUD.Auto),
			((77, 23), HUD.Help),
			]

	def __init__(self, game):
		self.game = game
		self.messages = []
		self.aim = None

	# Options for customizations.

	def get_map_shift(self):
		return Point(0, 0)
	def get_message_line_rect(self):
		return Rect(Point(0, 24), Size(80, 1))
	@functools.lru_cache()
	def get_viewport(self):
		return Size(61, 23)
	def get_viewrect(self):
		viewport = self.get_viewport()
		area_rect = self.game.scene.get_area_rect()
		if area_rect.size.width <= viewport.width and area_rect.size.height <= viewport.height:
			return area_rect
		player = self.game.scene.get_player()
		if player:
			pos = self.game.scene.get_global_pos(self.game.scene.get_player())
			self._old_pos = pos
		else:
			pos = self._old_pos
		viewport_center = Point(*(viewport // 2))
		Log.debug('Viewport: {0}x{1} at pos {2}'.format(viewport_center, viewport, pos))
		return Rect(pos - viewport_center, viewport)
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
			try:
				ui.window.set_cell(screen_pos, sprite.sprite[0])
			except: # pragma: no cover
				raise RuntimeError('Failed to draw sprite @{0} (screen {1}): {2} ({3})'.format(world_pos, screen_pos, sprite, cell_info))
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
	@_MainKeys.bind(list('hjklyubn'), lambda key:src.engine.ui.DIRECTION[str(key)])
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
		dialog = GodModeMenu(self.game)
		dialog.show(self)
	@_MainKeys.bind('i')
	def show_inventory(self):
		""" Show inventory. """
		dialog = Inventory(self.game.scene.get_player())
		dialog.show(self.loop)
	@_MainKeys.bind('d')
	def drop_item(self):
		""" Drop item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		dialog = Inventory(
				self.game.scene.get_player(),
				caption = "Select item to drop:",
				on_select = self.game.drop_item
			)
		dialog.show(self.loop)
	@_MainKeys.bind('e')
	def consume(self):
		""" Consume item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		dialog = Inventory(
				self.game.scene.get_player(),
				caption = "Select item to consume:",
				on_select = self.game.consume_item,
				)
		dialog.show(self.loop)
	@_MainKeys.bind('w')
	def wield(self):
		""" Wield item. """
		if not self.game.scene.get_player().inventory:
			self.game.fire_event(Events.InventoryIsEmpty())
			return
		dialog = Inventory(
				self.game.scene.get_player(),
				caption = "Select item to wield:",
				on_select = self.game.wield_item,
				)
		dialog.show(self.loop)
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
		dialog = Inventory(
				self.game.scene.get_player(),
				caption = "Select item to wear:",
				on_select = self.game.wear_item,
				)
		dialog.show(self.loop)
	@_MainKeys.bind('T')
	def take_off(self):
		""" Take item off. """
		self.game.take_off_item(self.game.scene.get_player())
	@_MainKeys.bind('E')
	def show_equipment(self):
		""" Show equipment. """
		dialog = Equipment(self.game, self.game.scene.get_player())
		dialog.show(self.loop)
	@_MainKeys.bind('q')
	def show_questlog(self):
		""" List current quests. """
		dialog = QuestLog(self.game.scene, list(self.game.scene.iter_active_quests()))
		dialog.show(self.loop)
	@_MainKeys.bind('C')
	def chat(self):
		""" Chat with NPC. """
		npcs = self.game.get_respondents(self.game.scene.get_player())
		if not npcs:
			return None
		def _chat_with_npc(npc):
			prompt, on_yes, on_no = self.game.chat(self.game.scene.get_player(), npc)
			if prompt:
				dialog = TradeDialogMode('"{0}" (y/n)'.format(prompt),
							on_yes=on_yes, on_no=on_no)
				dialog.show(self.loop)
				return None
		if len(npcs) > 1:
			dialog = DirectionDialogMode(on_direction=_chat_with_npc)
			dialog.show(self.loop)
			return None
		return _chat_with_npc(npcs[0])
	@_MainKeys.bind('M')
	def show_map(self):
		""" Show map. """
		dialog = MapScreen(self.game.scene, self.get_viewport())
		dialog.show(self.loop)
	@_MainKeys.bind('O')
	def open_close_doors(self):
		""" Open/close nearby doors. """
		self.game.toggle_nearby_doors(self.game.scene.get_player())

class ModalDialog(object):
	def close(self):
		self.window.grab_release()
		self.window.destroy()
		self.loop.redraw()
	def show(self, loop):
		self.loop = loop
		ui = loop.ui
		self.window = tkinter.Toplevel(ui.root)
		self.window.config(background=TkUI.BACKGROUND)
		button = tkinter.Button(
				self.window, text='Close',
				font=("Courier", ui._gui_size),
				command=self.close,
				)
		button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
		button.pack()

		self.create_window(ui)
		self.window.grab_set()
		self.window.transient(ui.root)
		try:
			self.window.wait_visibility()
		except tkinter.TclError: # window "..." was deleted before its visibility changed
			pass
	def create_window(self, ui):
		raise NotImplementedError()

class QuestLog(ModalDialog):
	def __init__(self, scene, quests):
		self.scene = scene
		self.quests = quests
	def create_window(self, ui):
		quests = []
		if not self.quests:
			quests.append("No current quests.")
		else:
			quests.append("Current quests:")
		for index, (npc, quest) in enumerate(self.quests):
			quests.append(npc.name + ' ' + npc.sprite.sprite + ' ' + "{0}: {1}".format(
				self.scene.get_str_location(npc), quest.summary(),
				))

		quest_list = tkinter.Label(
				self.window,
				text='\n'.join(quests),
				font=("Courier", ui._font_size),
				)
		quest_list.pack()
		quest_list.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

class GodModeMenu(ModalDialog):
	""" God mode options. """
	def __init__(self, game):
		self.game = game
	def create_window(self, ui):
		caption = tkinter.Label(
				self.window,
				text='Select God option:',
				font=("Courier", ui._font_size),
				)
		caption.pack()
		caption.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

		button = tkinter.Button(
				self.window, text='[{0}] Vision'.format('X' if self.game.god.vision else ' '),
				font=("Courier", ui._gui_size),
				command=self.vision,
				)
		button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
		button.pack()

		button = tkinter.Button(
				self.window, text='[{0}] NoClip'.format('X' if self.game.god.noclip else ' '),
				font=("Courier", ui._gui_size),
				command=self.noclip,
				)
		button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
		button.pack()

	def vision(self):
		""" See all. """
		self.game.god.toggle_vision()
		self.game.fire_event(Events.GodModeSwitched('vision', self.game.god.vision))
		self.close()
	def noclip(self):
		""" Walk through walls. """
		self.game.god.toggle_noclip()
		self.game.fire_event(Events.GodModeSwitched('noclip', self.game.god.noclip))
		self.close()

class DirectionDialogMode(ModalDialog):
	""" User prompt to pick direction in case where there are
	multiple options for some action.
	"""
	def __init__(self, on_direction=None):
		self.on_direction = on_direction
	def create_window(self, ui):
		caption = tkinter.Label(
				self.window,
				text="Too crowded. Chat in which direction?",
				font=("Courier", ui._font_size),
				)
		caption.pack()
		caption.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
		if self.on_direction:
			keys = [
					'yku',
					'h l',
					'bjn',
					]
			for keyline in keys:
				frame = tkinter.Frame(self.window)
				frame.pack()
				for key in keyline:
					if key == ' ':
						command = lambda:None
					else:
						command = lambda _key=key: self.on_direction(src.engine.ui.DIRECTION(_key))
					button = tkinter.Button(
							frame, text=key,
							command=command,
							)
					button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
					button.pack(side='left')

class Inventory(ModalDialog):
	""" Inventory menu.
	Supports prompting message.
	"""
	def __init__(self, actor, caption=None, on_select=None):
		""" Shows actor's inventory with optional prompt
		and callable action upon selecting an item.
		By default pressing any key will close the inventory view.
		Selector should accept params: (actor, item).
		"""
		self.actor = actor
		self.inventory = actor.inventory
		self.prompt = caption or 'Inventory:'
		self.on_select = on_select
	def update_prompt(self, value):
		self.prompt.config(text=value)
	def create_window(self, ui):
		self.prompt = tkinter.Label(
				self.window,
				text=self.prompt,
				font=("Courier", ui._font_size),
				)
		self.prompt.pack()
		self.prompt.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

		if not self.inventory:
			message = tkinter.Label(
					self.window,
					text = '(Empty)',
					font=("Courier", ui._font_size),
					)
			message.pack()
			message.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
			return
		accumulated = []
		for shortcut, item in zip(string.ascii_lowercase, self.inventory):
			for other in accumulated:
				if other[1].name == item.name:
					other[2] += 1
					break
			else:
				accumulated.append([shortcut, item, 1])
		columns = []
		for index, (shortcut, item, amount) in enumerate(accumulated):
			column = index // 20
			if column >= len(columns):
				frame = tkinter.Frame(self.window)
				frame.pack(side='left')
				frame.config(background=TkUI.BACKGROUND)
				columns.append(frame)
			index = index % 20

			text = item.sprite.sprite
			if amount > 1:
				text += ' - {0} (x{1})'.format(item.name, amount)
			else:
				text += ' - {0}'.format(item.name)
			button = tkinter.Button(
					columns[column], text=text,
					font=("Courier", ui._gui_size),
					command=lambda _key=shortcut: self.select(_key),
					)
			button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
			button.pack()

	def select(self, param):
		""" Select item and close inventory. """
		if not self.on_select:
			self.close()
			return
		index = ord(param) - ord('a')
		if index >= len(self.inventory):
			self.update_prompt("No such item ({0})".format(param))
			return
		if not self.on_select(self.actor, self.inventory[index]):
			return
		self.close()

class Equipment(ModalDialog):
	""" Equipment menu.
	"""
	def __init__(self, game, actor):
		self.game = game
		self.actor = actor
		self.done = False
	def create_window(self, ui):
		wielding = self.actor.wielding
		if wielding:
			wielding = wielding.name
		wearing = self.actor.wearing
		if wearing:
			wearing = wearing.name

		wielding = tkinter.Button(
				self.window,
				text='wielding - {0}'.format(wielding),
				font=("Courier", ui._font_size),
				command=self.wield,
				)
		wielding.pack()
		wielding.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

		wearing = tkinter.Button(
				self.window,
				text='wearing  - {0}'.format(wearing),
				font=("Courier", ui._font_size),
				command=self.wear,
				)
		wearing.pack()
		wearing.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
	def wield(self):
		""" Wield or unwield item. """
		if self.actor.wielding:
			self.game.unwield_item(self.actor)
			self.close()
			return
		dialog = Inventory(
				self.actor,
				caption = "Select item to wield:",
				on_select = self.game.wield_item,
				)
		dialog.show(self.loop)
		self.close()
	def wear(self):
		""" Wear or take off item. """
		if self.actor.wearing:
			self.game.take_off_item(self.actor)
			self.close()
			return
		dialog = Inventory(
				self.actor,
				caption = "Select item to wear:",
				on_select = self.game.wear_item,
				)
		dialog.show(self.loop)
		self.close()

class MapScreen(ModalDialog):
	""" Map of the surrounding area (if Scene allows). """
	def __init__(self, scene, size):
		self.scene = scene
		self.size = size
	def create_window(self, ui):
		area_map = self.scene.make_map(self.size)
		if not area_map:
			message = tkinter.Label(
					self.window,
					text='No map for current location.',
					font=("Courier", ui._font_size),
					)
			message.pack()
			message.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
			return
		output = Matrix(self.size, ' ')
		for pos in area_map:
			sprite = area_map.cell(pos)
			if not sprite:
				continue
			output.set_cell(pos, sprite.sprite)
		map_view = tkinter.Label(
				self.window,
				text=output.tostring(),
				font=("Courier", ui._font_size),
				)
		map_view.pack()
		map_view.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

class TradeDialogMode(ModalDialog):
	def __init__(self, question, on_yes=None, on_no=None):
		self.question = question
		self.on_yes = on_yes
		self.on_no = on_no
	def create_window(self, ui):
		caption = tkinter.Label(
				self.window,
				text=self.question,
				font=("Courier", ui._font_size),
				)
		caption.pack()
		caption.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)

		if self.on_yes:
			button = tkinter.Button(
					self.window, text='Yes',
					font=("Courier", ui._gui_size),
					command=self.on_yes,
					)
			button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
			button.pack()

		if self.on_no:
			button = tkinter.Button(
					self.window, text='No',
					font=("Courier", ui._gui_size),
					command=self.on_no,
					)
			button.config(background=TkUI.BACKGROUND, foreground=TkUI.FOREGROUND)
			button.pack()

class ModeLoop(object): # pragma: no cover -- TODO
	""" Main mode loop.
	Runs redraw/input until aborted by Mode.action().
	If .TRANSPARENT is not True, cleans screen before redrawing.
	"""
	def __init__(self, ui):
		self.ui = ui
		self.ui._loop = self
		self.mode = None
	def run(self, mode):
		""" Start loop from the given ("main") mode.
		Runs until the last mode is exited.
		"""
		self.mode = mode
		mode.loop = self
		self.redraw()
		self.ui.root.mainloop()
	def redraw(self):
		""" Redraws all modes, starting from the first non-transparent mode from the end of the current stack. """
		with self.ui.redraw(clean=True):
			self.mode.redraw(self.ui)
	def action(self, control=None):
		""" Perform user actions for the current stack of modes. """
		current_mode = self.mode
		mode = current_mode
		if not mode.game.scene.get_player():
			self.mode = None
			self.ui.root.after(10, self.ui.root.destroy)
			return False
		mode.game.perform_automovement()

		keymapping = mode.get_keymapping()
		if mode.messages:
			keymapping = None
		player = mode.game.scene.get_player()
		if not (player and player.is_alive()):
			keymapping = None
		if mode.game.in_automovement():
			keymapping = None

		if keymapping:
			if control is not None:
				control = keymapping.get(control, bind_self=mode)
				if callable(control):
					callback_args = mode.get_bind_callback_args() or []
					control = control(*callback_args)
			else:
				control = None

		result = not control
		if isinstance(control, clckwrkbdgr.tui.Key):
			if mode.messages:
				result = True
			player = mode.game.scene.get_player()
			if not (player and player.is_alive()):
				result = False
			mode.game.stop_automovement()
			result = True
		mode.game.process_others()

		if not result:
			self.mode = None
			self.ui.root.after(10, self.ui.root.destroy)
			return False
		self.redraw()
		if self.mode.game.in_automovement():
			self.ui.root.after(100, self.action)
		return True
