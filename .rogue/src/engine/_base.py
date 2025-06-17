class Game(object):
	""" Main object for the game mechanics.
	"""
	def generate(self): # pragma: no cover
		""" Should reset game and generate new state.
		Common pattern is create dummy Game object
		and then explicitly call generate().
		"""
		raise NotImplementedError()
	def load(self, reader): # pragma: no cover
		""" Should load game data from the stream/state.
		"""
		raise NotImplementedError()
	def save(self, reader): # pragma: no cover
		""" Should store game data to the reader/state.
		"""
		raise NotImplementedError()
	def is_finished(self): # pragma: no cover
		""" Should return True if game is completed/finished/failed
		and should reset, e.g. savefile should be deleted.
		Otherwise game keeps going and should be saved.
		"""
		raise NotImplementedError()
