from . import items, appliances, actors, terrain
from clckwrkbdgr import utils
from clckwrkbdgr.math.grid import Matrix

class Scene(object):
	""" Current physical map of terrain, objects, actors, etc.
	"""

	def load(self, stream):
		stream.set_meta_info('Terrain', {_.__name__:_ for _ in utils.all_subclasses(terrain.Terrain)})
		stream.set_meta_info('Items', {_.__name__:_ for _ in utils.all_subclasses(items.Item)})
		stream.set_meta_info('Appliances', {_.__name__:_ for _ in utils.all_subclasses(appliances.Appliance)})
		stream.set_meta_info('Actors', {_.__name__:_ for _ in utils.all_subclasses(actors.Actor)})

	def tostring(self, view_rect):
		result = Matrix(view_rect.size)
		for pos, cell_info in self.iter_cells(view_rect):
			result.set_cell(pos - view_rect.topleft, self.str_cell(pos, cell_info))
		return result.tostring()
	def str_cell(self, pos, cell_info=None):
		if not cell_info:
			cell_info = self.get_cell_info(pos)
		cell, objects, items, monsters = cell_info
		if monsters:
			return monsters[-1].sprite
		if items:
			return items[-1].sprite
		if objects:
			return objects[-1].sprite
		return cell.sprite

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
