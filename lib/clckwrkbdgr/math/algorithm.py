class Wave(object):
	""" Defines abstract wave algorithm on set of linkes nodes (like graph or matrix)
	from start until it reaches the target node.
	Calcultes path of nodes (including start and target) if possible.
	Create a subclass with specific implementation of abstract functions
	for specific functionality.
	>>> wave = CustomWave(start, stop)
	>>> path = wave.run()
	"""
	def is_linked(self, node_from, node_to): # pragma: no cover
		""" Should return True if node_to is directly reachable from node_from.
		Allows directional graphs when function is_linked(from, to) !== is_linked(to, from).
		"""
		raise NotImplementedError
	def get_links(self, node): # pragma: no cover
		""" Should return iterable of all nodes directly reachable from given node. """
		raise NotImplementedError
	def run(self, start, target, depth=10000):
		""" Parameter depth serves as safeguard. After that number of waves algorithm
		gives up if target is not reached yet and returns None.
		"""
		waves = [{start}]
		already_used = set()
		while depth > 0:
			depth -= 1
			closest = set(node for previous in waves[-1] for node in self.get_links(previous))
			new_wave = closest - already_used
			if not new_wave:
				return None
			if target in new_wave:
				path = [target]
				for wave in reversed(waves):
					path.insert(0, next(node for node in wave if self.is_linked(node, path[0])))
				return path
			already_used |= new_wave
			waves.append(new_wave)
		return None

def floodfill(start, spread_function):
	""" Fills area starting from 'start' and using spread_function(p) to iterate over next possible points to advance.
	Does not check if start is already 'filled', it should be checked by caller or spread_function.
	Yields generated values.
	"""
	already_affected = {start}
	last_wave = {start}
	yield start
	while last_wave:
		wave = set()
		for point in last_wave:
			wave |= set(spread_function(point))
		for point in wave - already_affected:
			yield point
		already_affected |= wave
		last_wave = wave
