from . import items, appliances, actors, terrain
from . import vision
from clckwrkbdgr import utils
from clckwrkbdgr.math.grid import Matrix
from .math import is_diagonal

class Scene(object):
	""" Current physical map of terrain, objects, actors, etc.
	"""

	def one_time(self): # pragma: no cover
		""" Should return True when scene is one-time entry only
		and should be discarded immediately on leave.
		By default all visited scenes are kept.
		"""
		return False
	def make_vision(self): # pragma: no cover
		""" Should init and return empty Vision object that supports this scene.
		"""
		return vision.OmniVision(self)
	def generate(self, id): # pragma: no cover
		""" Should generate scene for given map ID.
		"""
		raise NotImplementedError()
	def exit_actor(self, actor): # pragma: no cover
		""" Should remove actor from the scene and return it. """
		raise NotImplementedError()
	def enter_actor(self, actor, location): # pragma: no cover
		""" Should place actor on the scene at the specified location
		(value and interpretation may depend on concrete Scene implementation).
		If location is None, should pick the "default" location
		(also implementation-defined), e.g. dungeon entrance or stairs.
		"""
		raise NotImplementedError()
	def recalibrate(self, vantage_point, margin=None): # pragma: no cover
		""" Should re-adjust (if needed) internal grid in case
		if it dynamically loads/generates/unloads part of the map
		(e.g. endless grid or nested grid).
		Should make sure that area surrounding given vantage point
		is valid and adjusted properly.
		Optional margin size can specify distance (for both axis)
		to the edge of the world at which map should be forced
		to recalibrate. Up to implementation how to treat this value,
		usually it should be the size of player's character vision/action area.
		"""
		pass

	def load(self, stream):
		stream.set_meta_info('Terrain', {_.__name__:_ for _ in utils.all_subclasses(terrain.Terrain)})
		stream.set_meta_info('Items', {_.__name__:_ for _ in utils.all_subclasses(items.Item)})
		stream.set_meta_info('Appliances', {_.__name__:_ for _ in utils.all_subclasses(appliances.Appliance)})
		stream.set_meta_info('Actors', {_.__name__:_ for _ in utils.all_subclasses(actors.Actor)})

	def tostring(self, view_rect):
		result = Matrix(view_rect.size, ' ')
		for pos, cell_info in self.iter_cells(view_rect):
			result.set_cell(pos - view_rect.topleft, self.str_cell(pos, cell_info))
		return result.tostring()
	def str_cell(self, pos, cell_info=None):
		if not cell_info:
			cell_info = self.get_cell_info(pos)
		cell, objects, items, monsters = cell_info
		if monsters:
			return monsters[-1].sprite.sprite
		if items:
			return items[-1].sprite.sprite
		if objects:
			return objects[-1].sprite.sprite
		return cell.sprite.sprite if cell is not None else None

	def valid(self, pos): # pragma: no cover
		""" Returns True if specified position is valid within scene
		and can be addressed.
		"""
		raise NotImplementedError()
	def get_cell_info(self, pos, context=None): # pragma: no cover
		""" Should return cell info in form of tuples for given world position:
		(terrain, [objects on that cell], [items on that cell], [monsters on that cell]).
		Terrain may be None. Any list may be empty.
		Entities in lists should be sorted bottom-to-top.
		Monster list should include player if present.
		No visibility/remembered state should be checked at this stage. This is raw info.

		Additional context data may be passed with some cached calculations
		(usually within loops like iter_cells()).
		"""
	def iter_cells(self, view_rect): # pragma: no cover
		""" Should yield cell info for each position in the given boundaries:
		(world pos, cell info)
		See get_cell_info() for details.
		"""
		raise NotImplementedError()
	def get_player(self): # pragma: no cover
		""" Should return player-controlled actor character. """
		raise NotImplementedError()
	def cell(self, pos):
		""" Returns Terrain object at the specified position. """
		return self.get_cell_info(pos)[0]
	def iter_items_at(self, pos): # pragma: no cover
		""" Should iterate over all items at the specified position. """
		raise NotImplementedError()
	def iter_actors_at(self, pos, with_player=False): # pragma: no cover
		""" Should iterate over all actors at the specified position.
		If with_player is True, additionaly returns player characters.
		By default (False) returns only non-player actors.
		"""
		raise NotImplementedError()
	def iter_appliances_at(self, pos): # pragma: no cover
		""" Should iterate over all appliance objects at the specified position. """
		raise NotImplementedError()
	def iter_active_monsters(self): # pragma: no cover
		""" Should iterate over all actors that could act in the current turn
		(e.g. actors in some area around player, leaving all other intact).
		Could return player character.
		"""
		raise NotImplementedError()

	def get_global_pos(self, actor):
		""" Should return global pos for scenes where Actor.pos refers
		to some local zones and global pos should be calculated.
		"""
		return actor.pos
	def can_move(self, actor, pos):
		""" Should return True if actor can move onto terrain at pos
		(without checks for objects or other actors).
		Should consider diagonal movement if applicable.
		By default checks just passability of the target cell.
		"""
		return self.get_cell_info(pos)[0].passable
	def transfer_actor(self, actor, pos):
		""" Should transfer actor to a new location.
		Does not perform any check.
		Should be aware of internal terrain structure (if applicable).
		By default just changes Actor's .pos property.
		"""
		actor.pos = pos
	def is_passable(self, pos):
		""" Returns True is cell is passable (open for movement).
		Terrain should be .passable, as well as any appliances at the position.
		Also any actor is considered to be impassable (blocking movement).
		"""
		cell, objects, items, monsters = self.get_cell_info(pos)
		if not cell.passable:
			return False
		if monsters:
			return False
		if not all(obj.passable for obj in objects):
			return False
		return True
	def allow_movement_direction(self, from_point, to_point):
		""" Returns True, if current map allows direct movement from point to point. """
		if not is_diagonal(to_point - from_point):
			return True
		if not self.cell(from_point).allow_diagonal:
			return False
		if not self.cell(to_point).allow_diagonal:
			return False
		return True
	@classmethod
	def get_autoexplorer_class(cls):
		""" Should return class for free autoxploring on this Scene.
		Used by Game.automove()
		"""
		from . import auto
		return auto.AutoExplorer
