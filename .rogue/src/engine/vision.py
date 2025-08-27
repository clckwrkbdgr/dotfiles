class Vision(object):
	""" Basic vision/memory capabilities.
	Should support fields or vision and remembered/visited places.
	"""
	def __init__(self, scene):
		""" Creates vision field and memory for given scene.
		"""
		self.scene = scene
	def is_visible(self, pos): # pragma: no cover
		""" Should return True is position on map is visible.
		"""
		raise NotImplementedError()
	def is_explored(self, pos): # pragma: no cover
		""" Should return True if given position is visible or
		was visited and/or seen.
		"""
		raise NotImplementedError()
	def iter_important(self): # pragma: no cover
		""" Should yield dangerous/important objects/happenings
		in the current field of view (like monsters).
		Mostly used to stop/prevent automatic actions.
		"""
		raise NotImplementedError()
	def visit(self, actor): # pragma: no cover
		""" Should mark actor's position as visited along with every place visible from that position.
		Updates current field of vision.
		Should return iterable or yield new objects that come into vision.
		"""
		raise NotImplementedError()

class OmniVision(Vision):
	""" Most primitive Vision: everything is visible
	and explored from the start.
	"""
	def save(self, stream): pass
	def load(self, stream): pass
	def is_visible(self, pos): return True
	def is_explored(self, pos): return True
	def visit(self, actor): return []
	def iter_important(self): return []
