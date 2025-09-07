import inspect
import clckwrkbdgr.utils

class MakeEntity:
	""" Creates builders for bare-properties-based classes to create subclass in one line.
	>>> make_weapon = MakeEntity(Item, '_sprite _name _attack')
	>>> make_weapon('Dagger', Sprite('(', None), 'dagger', 1)
	"""
	def __init__(self, base_classes, *properties):
		""" Properties are either list of strings, or a single strings with space-separated identifiers. """
		self.base_classes = base_classes if clckwrkbdgr.utils.is_collection(base_classes) else (base_classes,)
		self.properties = properties
		if len(self.properties) == 1 and ' ' in self.properties[0]:
			self.properties = self.properties[0].split()
	def __call__(self, class_name, *values):
		""" Creates class object and puts it into global namespace.
		Values should match properties given at init.
		"""
		assert len(self.properties) == len(values), len(values)
		entity_class = type(class_name, self.base_classes, dict(zip(self.properties, values)))
		caller_globals = inspect.currentframe().f_back.f_globals
		caller_globals[class_name] = entity_class
		return entity_class
