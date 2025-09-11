import sys
import functools
import random
import math
import string
import logging
from collections import namedtuple
import curses
import clckwrkbdgr.logging
Log = logging.getLogger('rogue')
from clckwrkbdgr.math import Point, Rect, Size, Matrix, sign, distance
from clckwrkbdgr.math.grid import NestedGrid
from clckwrkbdgr import xdg, utils
import clckwrkbdgr.serialize.stream
import clckwrkbdgr.tui
from src import engine
from src.engine import builders, scene
from src.engine import events, auto, vision
import src.engine.actors, src.engine.items, src.engine.appliances, src.engine.terrain
from src.engine.items import Item
from src.engine.terrain import Terrain
from src.engine.actors import Monster, EquippedMonster
from src.engine import ui
from src.engine import ui as UI
from src.engine.ui import Sprite
from src.engine import Events
from src.world import overworld
from hud import *
from terrain import *
from items import *
from objects import *
from monsters import *
from quests import *

SAVEFILE_VERSION = 15

class Builder(object):
	class Mapping(TerrainMapping, QuestMapping, ItemMapping, MonsterMapping, ObjectMapping):
		pass

class Forest(Builder, overworld.Forest): pass
class Desert(Builder, overworld.Desert): pass
class Thundra(Builder, overworld.Thundra): pass
class Marsh(Builder, overworld.Marsh): pass

class NoOneToChat(events.Event): FIELDS = ''
class NoOneToChatInDirection(events.Event): FIELDS = ''
class TooMuchQuests(events.Event): FIELDS = ''
class ChatThanks(events.Event): FIELDS = ''
class ChatComeLater(events.Event): FIELDS = ''
class ChatQuestReminder(events.Event): FIELDS = 'color item'

events.Events.on(NoOneToChat)(lambda _:'No one to chat with.')
events.Events.on(NoOneToChatInDirection)(lambda _:'No one to chat with in that direction.')
events.Events.on(TooMuchQuests)(lambda _:"Too much quests already.")
events.Events.on(ChatThanks)(lambda _:'"Thanks. Here you go."')
events.Events.on(ChatComeLater)(lambda _:'"OK, come back later if you want it."')
events.Events.on(ChatQuestReminder)(lambda _:'"Come back with {0} {1}."'.format(_.color, _.item))

Color = namedtuple('Color', 'fg attr dweller monster')
class Game(engine.Game):
	COLORS = {
			'black': Color(curses.COLOR_BLACK, 0, False, False),
			'red': Color(curses.COLOR_RED, 0, True, True),
			'green': Color(curses.COLOR_GREEN, 0, True, True),
			'blue': Color(curses.COLOR_BLUE, 0, True, True),
			'yellow': Color(curses.COLOR_YELLOW, 0, True, True),
			'cyan': Color(curses.COLOR_CYAN, 0, True, True),
			'magenta': Color(curses.COLOR_MAGENTA, 0, True, True),
			'white': Color(curses.COLOR_WHITE, 0, True, True),
			'bold_black': Color(curses.COLOR_BLACK, curses.A_BOLD, True, True),
			'bold_red': Color(curses.COLOR_RED, curses.A_BOLD, True, True),
			'bold_green': Color(curses.COLOR_GREEN, curses.A_BOLD, True, True),
			'bold_blue': Color(curses.COLOR_BLUE, curses.A_BOLD, True, True),
			'bold_yellow': Color(curses.COLOR_YELLOW, curses.A_BOLD, True, True),
			'bold_cyan': Color(curses.COLOR_CYAN, curses.A_BOLD, True, True),
			'bold_magenta': Color(curses.COLOR_MAGENTA, curses.A_BOLD, True, True),
			'bold_white': Color(curses.COLOR_WHITE, curses.A_BOLD, False, True),
			}
	def make_scene(self, scene_id):
		return overworld.Scene(utils.all_subclasses(Builder))
	def make_player(self):
		return Rogue(None)

DialogKeys = clckwrkbdgr.tui.Keymapping()
DialogKeys.map(list('yY'), True)

QuestLogKeys = clckwrkbdgr.tui.Keymapping()
QuestLogKeys.map(clckwrkbdgr.tui.Key.ESCAPE, 'cancel')

def main(ui):
	for name, color in Game.COLORS.items():
		ui.init_color(name, color.fg, color.attr)

	game = Game()
	savefile = clckwrkbdgr.serialize.stream.Savefile(xdg.save_data_path('dotrogue')/'rogue.sav')
	with savefile.get_reader() as reader:
		if reader:
			assert reader.version == SAVEFILE_VERSION, (reader.version, SAVEFILE_VERSION, savefile.filename)
			game.load(reader)
		else:
			game.generate(None)

	main_game = MainGameMode(game)
	loop = clckwrkbdgr.tui.ModeLoop(ui)
	loop.run(main_game)
	if not game.is_finished():
		with savefile.save(SAVEFILE_VERSION) as writer:
			game.save(writer)
	else:
		savefile.unlink()

class MainGameMode(MainGame):
	@ui.MainGame.Keys.bind('C')
	def char(self):
		game = self.game
		player_pos = game.scene.get_player_coord().get_global(game.scene.world)
		if True:
			npcs = [
					monster for monster_pos, monster
					in self.game.scene.all_monsters()
					if max(abs(monster_pos.x - player_pos.x), abs(monster_pos.y - player_pos.y)) <= 1
					and isinstance(monster, Dweller)
					]
			questing = [
					npc for _, npc in self.game.scene.all_monsters()
					if isinstance(npc, Dweller)
					and npc.quest
					]
			if not npcs:
				self.game.fire_event(NoOneToChat())
			elif len(questing) > 20:
				self.game.fire_event(TooMuchQuests())
			else:
				if len(npcs) > 1:
					def _on_direction(direction):
						dest = player_pos + dialog.answer
						npcs = [npc for npc in npcs if npc.pos == dest]
						return self._chat_with_npcs(npcs)
					return DirectionDialogMode(on_direction=_on_direction)
				return self._chat_with_npcs(npcs)
	def _chat_with_npcs(self, npcs):
		if True:
			if True:
				if npcs:
					npc = npcs[0]
					return self._chat_with_npc(npc)
				else:
					self.game.fire_event(NoOneToChatInDirection())
	def _chat_with_npc(self, npc):
		game = self.game
		if True:
			if True:
				if True:
					if npc.quest:
						required_amount, required_name, bounty = npc.quest
						have_required_items = list(
								game.scene.get_player().iter_items(ColoredSkin, name=required_name),
								)[:required_amount]
						if len(have_required_items) >= required_amount:
							def _on_yes():
								self.game.fire_event(ChatThanks())
								for item in have_required_items:
									game.scene.get_player().drop(item)
								if game.scene.get_player().hp == game.scene.get_player().max_hp:
									game.scene.get_player().hp += bounty
								game.scene.get_player()._max_hp += bounty
								npc.quest = None
							def _on_no():
								self.game.fire_event(ChatComeLater())
							return TradeDialogMode('"You have {0} {1}. Trade it for +{2} max hp?" (y/n)'.format(*(npc.quest)),
										on_yes=_on_yes, on_no=_on_no)
						else:
							self.game.fire_event(ChatQuestReminder(*(npc.quest)))
					else:
						if not npc.prepared_quest:
							amount = 1 + random.randrange(3)
							bounty = max(1, amount // 2 + 1)
							colors = [name for name, color in game.COLORS.items() if color.monster]
							color = random.choice(colors).replace('_', ' ') + ' skin'
							npc.prepared_quest = (amount, color, bounty)
						def _on_yes():
							npc.quest = npc.prepared_quest
							npc.prepared_quest = None
						def _on_no():
							self.game.fire_event(ChatComeLater())
						return TradeDialogMode('"Bring me {0} {1}, trade it for +{2} max hp, deal?" (y/n)'.format(*(npc.prepared_quest)),
										 on_yes=_on_yes, on_no=_on_no)
	@ui.MainGame.Keys.bind('q')
	def show_questlog(self):
		game = self.game
		if True:
			questing = [
					(coord, npc) for coord, npc in self.game.scene.all_monsters(raw=True)
					if isinstance(npc, Dweller)
					and npc.quest
					]
			quest_log = QuestLog(questing)
			return quest_log

DirectionKeys = clckwrkbdgr.tui.Keymapping()
class DirectionDialogMode(clckwrkbdgr.tui.Mode):
	TRANSPARENT = True
	KEYMAPPING = DirectionKeys
	def __init__(self, on_direction=None):
		self.on_direction = on_direction
	def redraw(self, ui):
		ui.print_line(24, 0, " " * 80)
		ui.print_line(24, 0, "Too crowded. Chat in which direction?")
	@DirectionKeys.bind(list('hjklyubn'), lambda key:UI.DIRECTION[str(key)])
	def choose_direction(self, direction):
		if self.on_direction:
			return self.on_direction(direction)
		return False
	def action(self, control):
		return False

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

class QuestLog(clckwrkbdgr.tui.Mode):
	TRANSPARENT = False
	KEYMAPPING = QuestLogKeys
	def __init__(self, quests):
		self.quests = quests
	def redraw(self, ui):
		if not self.quests:
			ui.print_line(0, 0, "No current quests.")
		else:
			ui.print_line(0, 0, "Current quests:")
		for index, (coord, npc) in enumerate(self.quests):
			ui.print_line(index + 1, 0, "@ {2}: Bring {0} {1}.".format(
				npc.quest[0],
				npc.quest[1],
				coord,
				))
	def action(self, control):
		return control != 'cancel'

import click
@click.command()
@click.option('-d', '--debug', is_flag=True)
def cli(debug=False):
	if debug:
		clckwrkbdgr.logging.init(
			'rogue', debug=True, filename='rogue.log', stream=None,
			)
	with clckwrkbdgr.tui.Curses() as ui:
		main(ui)

if __name__ == '__main__':
	cli()
