from src.engine.ui import Sprite
from src.engine.terrain import Terrain

class Impassable(Terrain):
	_passable = False

class Void(Impassable):
	_name = 'void'
	_sprite = Sprite(' ', 'black')

class Wall(Impassable):
	_name = 'wall'
	_sprite = Sprite('#', 'white')
class WallH(Impassable):
	_name = 'wall'
	_sprite = Sprite("-", 'white')
class WallV(Impassable):
	_name = 'wall'
	_sprite = Sprite("|", 'white')
class Corner(Impassable):
	_name = 'corner'
	_sprite = Sprite("+", 'white')

class Door(Terrain):
	_name = 'door'
	_sprite = Sprite("+", 'yellow')
class RogueDoor(Terrain):
	_name = 'door'
	_sprite = Sprite("+", 'bold_black')
	_allow_diagonal=False
	_dark=True
class Passage(Terrain):
	_name = 'passage'
	_sprite = Sprite("#", 'white')
class RoguePassage(Terrain):
	_name = 'passage'
	_sprite = Sprite("#", 'bold_black')
	_allow_diagonal=False
	_dark=True

class Floor(Terrain):
	_name = 'floor'
	_sprite = Sprite('.', 'white')
class TunnelFloor(Terrain):
	_name = 'floor'
	_sprite = Sprite(".", 'white')
	_allow_diagonal=False

class Water(Terrain):
	_name = 'water'
	_sprite = Sprite("~", 'blue')
class Bog(Terrain):
	_name = 'bog'
	_sprite = Sprite('~', 'green')
class Bush(Terrain):
	_name = 'bush'
	_sprite = Sprite('"', 'bold_green')
class DeadTree(Terrain):
	_name = 'dead tree'
	_sprite = Sprite('&', 'yellow')
class FrozenGround(Terrain):
	_name = 'frozen ground'
	_sprite = Sprite('.', 'white')
class Grass(Terrain):
	_name = 'grass'
	_sprite = Sprite('.', 'green')
class Ice(Terrain):
	_name = 'ice'
	_sprite = Sprite('.', 'cyan')
class Plant(Terrain):
	_name = 'plant'
	_sprite = Sprite('"', 'green')
class Sand(Terrain):
	_name = 'sand'
	_sprite = Sprite('.', 'bold_yellow')
class Snow(Terrain):
	_name = 'show'
	_sprite = Sprite('.', 'bold_white')
class Swamp(Terrain):
	_name = 'swamp'
	_sprite = Sprite('~', 'cyan')
class Tree(Terrain):
	_name = 'tree'
	_sprite = Sprite('&', 'bold_green')
class SwampTree(Terrain):
	_name = 'swamp tree'
	_sprite = Sprite('&', 'green')

class Rock(Impassable):
	_name = 'rock'
	_sprite = Sprite('^', 'yellow')

class TerrainMapping:
	bog = Bog()
	bush = Bush()
	corner = Corner()
	dead_tree = DeadTree()
	door = Door()
	rogue_door = RogueDoor()
	floor = Floor()
	frozen_ground = FrozenGround()
	grass = Grass()
	ice = Ice()
	passage = Passage()
	plant = Plant()
	rock = Rock()
	rogue_passage = RoguePassage()
	tunnel = RoguePassage()
	sand = Sand()
	snow = Snow()
	swamp = Swamp()
	swamp_tree = SwampTree()
	tree = Tree()
	tunnel_floor = TunnelFloor()
	void = Void()
	wall = Wall()
	wall_h = WallH()
	wall_v = WallV()
	water = Water()
