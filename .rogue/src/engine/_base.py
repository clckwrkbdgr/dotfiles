class Game(object):
	""" Main object for the game mechanics.
	"""
	def is_finished(self): # pragma: no cover
		""" Should return True if game is completed/finished/failed
		and should reset, e.g. savefile should be deleted.
		Otherwise game keeps going and should be saved.
		"""
		raise NotImplementedError()
