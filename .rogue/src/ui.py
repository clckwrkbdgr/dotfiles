from __future__ import absolute_import
import functools
from collections import namedtuple
import curses, curses.ascii
import logging
Log = logging.getLogger('rogue')
from . import game
from clckwrkbdgr.math import Point, Direction, Rect, Size
from clckwrkbdgr import utils
import clckwrkbdgr.tui
import clckwrkbdgr.text
from clckwrkbdgr.tui import Key, Keymapping
from .engine.events import Events
from .engine import ui, actors
from . import engine
from .engine.ui import Sprite

class MainGame(ui.MainGame):
	INDICATORS = [
			ui.Indicator((0, 24), 11, lambda self: 'hp: {0:>{1}}/{2}'.format(
				self.game.scene.get_player().hp,
				len(str(self.game.scene.get_player().max_hp)),
				self.game.scene.get_player().max_hp) if self.game.scene.get_player() else '[DEAD] Press Any Key...'),
			ui.Indicator((12, 24), 7, lambda self: 'here: {0}'.format(
				next(self.game.scene.iter_items_at(self.game.scene.get_player().pos), None).sprite.sprite,
				) if self.game.scene.get_player() and next(self.game.scene.iter_items_at(self.game.scene.get_player().pos), None) else ''),
			ui.Indicator((20, 24), 7, lambda self: 'inv: {0:>2}'.format(
				''.join(item.sprite.sprite for item in self.game.scene.get_player().inventory)
				if len(self.game.scene.get_player().inventory) <= 2
				else len(self.game.scene.get_player().inventory)
				) if self.game.scene.get_player() and self.game.scene.get_player().inventory else ''
					 ),
			ui.Indicator((28, 24), 6, lambda self: '[auto]' if self.game.in_automovement() else ''),
			ui.Indicator((34, 24), 5, lambda self: '[vis]' if self.game.god.vision else ''),
			ui.Indicator((39, 24), 6, lambda self: '[clip]' if self.game.god.noclip else ''),
			ui.Indicator((77, 24), 3, lambda self: '[?]'),
			]

	def get_map_shift(self):
		return Point(0, 1)
	def get_viewrect(self):
		return self.game.scene.get_area_rect()
	def get_message_line_rect(self):
		return Rect(Point(0, 0), Size(80, 1))
	@Events.on(engine.Events.Welcome)
	def on_new_game(self, event):
		return ''
	@Events.on(engine.Events.WelcomeBack)
	def on_load_game(self, event): # pragma: no cover
		return ''
	@Events.on(engine.Events.Discover)
	def on_discovering(self, event):
		if hasattr(event.obj, 'name'):
			return '{0}!'.format(event.obj.name)
		else: # pragma: no cover
			return '{0}!'.format(event.obj)
	@Events.on(engine.Events.AutoStop)
	def on_auto_stop(self, event): # pragma: no cover
		if isinstance(event.reason[0], actors.Actor):
			return 'monsters!'
		else:
			return '{0}!'.format(event.reason[0])
	@Events.on(engine.Events.NothingToPickUp)
	def on_nothing_to_pick_up(self, event): # pragma: no cover
		return ''
	@Events.on(engine.Events.Attack)
	def on_attack(self, event): # pragma: no cover
		return '{0} x> {1}.'.format(event.actor.name, event.target.name)
	@Events.on(engine.Events.Health)
	def on_health_change(self, event):
		return '{0}{1:+}hp.'.format(event.target.name, event.diff)
	@Events.on(engine.Events.Death)
	def on_death(self, event): # pragma: no cover
		return '{0} dies.'.format(event.target.name)
	@Events.on(engine.Events.Move)
	def on_movement(self, event): # pragma: no cover
		if event.actor != self.game.scene.get_player():
			return '{0}...'.format(event.actor.name)
	@Events.on(engine.Events.Descend)
	def on_descending(self, event): # pragma: no cover
		return '{0} V...'.format(event.actor.name)
	@Events.on(engine.Events.BumpIntoTerrain)
	def on_bumping(self, event): # pragma: no cover
		if event.actor != self.game.scene.get_player():
			return '{0} bumps.'.format(event.actor.name)
	@Events.on(engine.Events.InventoryIsEmpty)
	def on_empty_inventory(self, event): # pragma: no cover
		return ''
	@Events.on(engine.Events.GrabItem)
	def on_grabbing(self, event):
		return '{0} ^^ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(engine.Events.DropItem)
	def on_dropping(self, event): # pragma: no cover
		return '{0} VV {1}.'.format(event.actor.name, event.item.name)
	@Events.on(engine.Events.ConsumeItem)
	def on_consuming(self, event):
		return '{0} <~ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(engine.Events.NotConsumable)
	def on_not_consuming(self, event):
		return 'X {0}.'.format(event.item.name)
	@Events.on(engine.Events.Wield)
	def on_equipping(self, event):
		return '{0} <+ {1}.'.format(event.actor.name, event.item.name)
	@Events.on(engine.Events.Unwield)
	def on_unequipping(self, event):
		return '{0} +> {1}.'.format(event.actor.name, event.item.name)

	@ui.MainGame.Keys.bind('e')
	def consume(self):
		""" Consume item. """
		return ui.Inventory(
				self.game.scene.get_player(),
				caption = "Select item to consume:",
				on_select = self.game.consume_item,
				)
	@ui.MainGame.Keys.bind('E')
	def show_equipment(self):
		""" Show equipment. """
		return Equipment(self.game)

EquipmentKeys = Keymapping()
class Equipment(clckwrkbdgr.tui.Mode):
	""" Equipment menu.
	"""
	KEYMAPPING = EquipmentKeys
	def __init__(self, game):
		self.game = game
		self.done = False
	def redraw(self, ui):
		game = self.game
		wielding = game.scene.get_player().wielding
		if wielding:
			wielding = wielding.name
		ui.print_line(0, 0, 'wielding [a] - {0}'.format(wielding))
	def action(self, done):
		return not (done or self.done)
	@EquipmentKeys.bind('a')
	def wield(self):
		""" Wield or unwield item. """
		if self.game.scene.get_player().wielding:
			self.game.unwield_item(self.game.scene.get_player())
			return True
		self.done = True
		return ui.Inventory(
				self.game.scene.get_player(),
				caption = "Select item to wield:",
				on_select = self.game.wield_item,
				)
	@EquipmentKeys.bind(clckwrkbdgr.tui.Key.ESCAPE)
	def close(self):
		""" Close by Escape. """
		return True
