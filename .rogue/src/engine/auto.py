class AutoMovement(object):
	""" Base class for any automovement mode.
	Supports both movement with target destination
	and endless auto-exploration modes.
	"""
	def next(self): # pragma: no cover
		""" Should return next movement shift
		or None, if automovement is finished.
		"""
		raise NotImplementedError()
