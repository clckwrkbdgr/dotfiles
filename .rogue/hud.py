from collections import namedtuple
import functools
import logging
import curses
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Rect, Size, Point
from src.engine import events, actors, Events, ui

Color = namedtuple('Color', 'fg attr')
COLORS = {
		'black': Color(curses.COLOR_BLACK, 0),
		'red': Color(curses.COLOR_RED, 0),
		'green': Color(curses.COLOR_GREEN, 0),
		'blue': Color(curses.COLOR_BLUE, 0),
		'yellow': Color(curses.COLOR_YELLOW, 0),
		'cyan': Color(curses.COLOR_CYAN, 0),
		'magenta': Color(curses.COLOR_MAGENTA, 0),
		'white': Color(curses.COLOR_WHITE, 0),
		'bold_black': Color(curses.COLOR_BLACK, curses.A_BOLD),
		'bold_red': Color(curses.COLOR_RED, curses.A_BOLD),
		'bold_green': Color(curses.COLOR_GREEN, curses.A_BOLD),
		'bold_blue': Color(curses.COLOR_BLUE, curses.A_BOLD),
		'bold_yellow': Color(curses.COLOR_YELLOW, curses.A_BOLD),
		'bold_cyan': Color(curses.COLOR_CYAN, curses.A_BOLD),
		'bold_magenta': Color(curses.COLOR_MAGENTA, curses.A_BOLD),
		'bold_white': Color(curses.COLOR_WHITE, curses.A_BOLD),
		}

events.Events.on(Events.Welcome)(lambda _:'Welcome!')
events.Events.on(Events.WelcomeBack)(lambda _:'Welcome back!')
events.Events.on(Events.NothingToPickUp)(lambda _:'Nothing to pick up here.')
events.Events.on(Events.InventoryIsFull)(lambda _: "Inventory is full! Cannot pick up {item}".format(item=event.item.name))
events.Events.on(Events.GrabItem)(lambda _:'{0} picks up {1}.'.format(_.actor.name, _.item.name))
events.Events.on(Events.InventoryIsEmpty)(lambda _:'Inventory is empty.')
events.Events.on(Events.NotConsumable)(lambda _:'Cannot consume {0}.'.format(_.item.name))
events.Events.on(Events.DropItem)(lambda _:'{0} drops {1}.'.format(_.actor.name.title(), _.item.name))
@events.Events.on(Events.BumpIntoTerrain)
def bumps_into_terrain(event):
	if not isinstance(event.actor, actors.Player):
		return "{Who} bumps.".format(Who=event.actor.name.title())
events.Events.on(Events.Move)(lambda _:None)
events.Events.on(Events.Health)(lambda _:'{0} {1:+}hp.'.format(_.target.name, _.diff))
events.Events.on(Events.BumpIntoActor)(lambda _:'{0} bumps into {1}.'.format(_.actor.name.title(), _.target.name))
events.Events.on(Events.Attack)(lambda _:'{0} hits {1} for {2}hp.'.format(_.actor.name.title(), _.target.name, _.damage))
events.Events.on(Events.StareIntoVoid)(lambda _:'The void gazes back.')
events.Events.on(Events.GodModeSwitched)(lambda event:"God {name} {state}".format(name=event.name, state=event.state))
events.Events.on(Events.NeedKey)(lambda event:"Cannot be opened without {0}!".format(event.key.__name__))

@events.Events.on(Events.Discover)
def on_discover(event):
	if hasattr(event.obj, 'name'):
		return '{0}!'.format(event.obj.name)
	else:
		return '{0}!'.format(event.obj)

@events.Events.on(Events.AutoStop)
def stop_auto_activities(event):
	if isinstance(event.reason[0], actors.Actor):
		return 'There are monsters nearby!'
	return 'There are {0} nearby!'.format(', '.join(map(str, event.reason)))

@events.Events.on(Events.Death)
def monster_is_dead(_):
	if isinstance(_.target, actors.Player):
		return 'You died!!!'
	return '{0} dies.'.format(_.target.name.title())

events.Events.on(Events.Ascend)(lambda event:"Going up...")
events.Events.on(Events.Descend)(lambda event:"Going down...")
events.Events.on(Events.CannotDescend)(lambda event:"Cannot dig through the ground.")
events.Events.on(Events.CannotAscend)(lambda event:"Cannot reach the ceiling from here.")
events.Events.on(Events.ConsumeItem)(lambda event:"{actor} consumed {item}.".format(actor=event.actor.name.title(), item=event.item.name))

events.Events.on(Events.NotWielding)(lambda event:"Already wielding nothing.")
events.Events.on(Events.Unwield)(lambda event:"{actor} unwields {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.Wield)(lambda event:"{actor} wield {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.NotWearable)(lambda event:"Cannot wear {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.NotWearing)(lambda event:"Already wearing nothing.")
events.Events.on(Events.TakeOff)(lambda event:"{actor} takes off {item}.".format(actor=event.actor.name.title(), item=event.item.name))
events.Events.on(Events.Wear)(lambda event:"{actor} wears {item}.".format(actor=event.actor.name.title(), item=event.item.name))

events.Events.on(Events.NoOneToChat)(lambda _:'No one to chat with.')
events.Events.on(Events.NoOneToChatInDirection)(lambda _:'No one to chat with in that direction.')
events.Events.on(Events.TooMuchQuests)(lambda _:"Too much quests already.")
events.Events.on(Events.ChatThanks)(lambda _:'"Thanks. Here you go."')
events.Events.on(Events.ChatComeLater)(lambda _:'"OK, come back later if you want it."')
events.Events.on(Events.ChatQuestReminder)(lambda _:'"{0}"'.format(_.message))


del globals()['Events'] # FIXME to prevent namespace pollution in the main module

class _HUD(object):
	@classmethod
	def pos(cls, self):
		if not self.game.scene.get_player():
			return None
		if hasattr(self.game.scene, 'get_player_coord'):
			coord = self.game.scene.get_player_coord()
			return "@{0:02X}.{1:X}.{2:X};{3:02X}.{4:X}.{5:X}".format(
				coord.values[0].x, coord.values[1].x, coord.values[2].x,
				coord.values[0].y, coord.values[1].y, coord.values[2].y,
				)
		pos = self.game.scene.get_global_pos(self.game.scene.get_player())
		return 'X:{x} Y:{y}  '.format(x=pos.x, y=pos.y)
	@classmethod
	def inventory(cls, self):
		if not self.game.scene.get_player() or not self.game.scene.get_player().inventory:
			return None
		if len(self.game.scene.get_player().inventory) <= 2:
			return ''.join(item.sprite.sprite for item in self.game.scene.get_player().inventory)
		return len(self.game.scene.get_player().inventory)
	@classmethod
	def here(cls, self):
		pos = self.game.scene.get_global_pos(self.game.scene.get_player())
		cell, objects, items, _  = self.game.scene.get_cell_info(pos)
		if items:
			return items[-1].sprite.sprite
		if objects:
			return objects[-1].sprite.sprite
		return None

class HUD(_HUD):
	Time = ui.CaptionedIndicator("T", 23, lambda self:self.game.playing_time)
	Depth = ui.CaptionedIndicator("Depth", 20, lambda dungeon: dungeon.game.current_scene_id)
	Pos = ui.Indicator(29, _HUD.pos)
	HP = ui.CaptionedIndicator("hp", 7, lambda self:"{0:>{1}}/{2}".format(
		self.game.scene.get_player().hp,
		len(str(self.game.scene.get_player().max_hp)),
		self.game.scene.get_player().max_hp) if self.game.scene.get_player() else "[DEAD]")
	Inventory = ui.CaptionedIndicator("inv", 2, _HUD.inventory)
	Here = ui.CaptionedIndicator("here", 1, _HUD.here)
	Wear = ui.CaptionedIndicator("Wear", 10, lambda dungeon: (dungeon.game.scene.get_player().wearing.name if dungeon.game.scene.get_player() and dungeon.game.scene.get_player().wearing else None))
	Wield = ui.CaptionedIndicator("Wld", 10, lambda dungeon: (dungeon.game.scene.get_player().wielding.name if dungeon.game.scene.get_player() and dungeon.game.scene.get_player().wielding else None))

	Auto = ui.Indicator(6, lambda self: '[auto]' if self.game.in_automovement() else '')
	GodVision = ui.Indicator(5, lambda self: '[vis]' if self.game.god.vision else '')
	GodNoclip = ui.Indicator(6, lambda self: '[clip]' if self.game.god.noclip else '')
	Help = ui.Indicator(3, lambda self: '[?]')

class MainGame(ui.MainGame):
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

	@functools.lru_cache()
	def get_viewport(self):
		viewport = Rect((0, 0), (61, 23))
		center = Point(*(viewport.size // 2))
		return Rect((-center.x, -center.y), viewport.size)

	def get_viewrect(self):
		viewport = self.get_viewport()
		area_rect = self.game.scene.get_area_rect()
		if area_rect.size.width <= viewport.size.width and area_rect.size.height <= viewport.size.height:
			return area_rect
		player = self.game.scene.get_player()
		if player:
			pos = self.game.scene.get_global_pos(self.game.scene.get_player())
			self._old_pos = pos
		else:
			pos = self._old_pos
		Log.debug('Viewport: {0} at pos {1}'.format(viewport, pos))
		return Rect(pos + viewport.topleft, viewport.size)
	def get_map_shift(self):
		return Point(0, 0)
	def get_message_line_rect(self):
		return Rect(Point(0, 24), Size(80, 1))
