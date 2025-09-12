import six, inspect

class Quest(object):
	""" Base class for any quest.
	"""
	_metainfo_key = 'Quests'
	def __init__(self):
		""" Creates prepated inactive quest by default.
		Use .activate() to actually start quest.
		"""
		self._active = False
	def is_active(self):
		return self._active
	def activate(self):
		self._active = True
	def save(self, writer):
		""" Default implementation writes only class name and active state.
		Override to write additional subclass-specific properties.
		Don't forget to call super().save()!
		"""
		writer.write(type(self).__name__)
		writer.write(self._active)
	@classmethod
	def load(cls, reader):
		""" Loads info about object (class name/active state), constructs actual instance
		and optionally loads subclass-specific data.
		Classes are serialized as their class names, so reader metainfo with key 'Quests'
		should be a dict-like object which stores all required classes under their class names.
		Subclasses should have default c-tor.
		Subclasses should override this method as non-classmethod (regular instance method)
		which loads subclass-specific data only.
		"""
		type_name = reader.read()
		registry = reader.get_meta_info(cls._metainfo_key)
		obj_type = registry[type_name]
		assert obj_type is cls or issubclass(obj_type, cls)
		obj = obj_type()
		obj._active = reader.read_bool()
		if six.PY2: # pragma: no cover -- TODO
			is_overridden_as_instance_method = obj_type.load.__self__ is not None
		else: # pragma: no cover -- TODO
			is_overridden_as_instance_method = inspect.ismethod(obj_type.load)
		if not is_overridden_as_instance_method:
			obj.load(reader)
		return obj

	def summary(self): # pragma: no cover
		""" Short summary (1 line). """
		raise NotImplementedError()
	def init_prompt(self): # pragma: no cover
		""" Initial prompt to start quest.
		Should expect answers Y/N.
		"""
		raise NotImplementedError()
	def reminder(self): # pragma: no cover
		""" Reminder message about quest when chatting with questgiver.
		"""
		raise NotImplementedError()
	def complete_prompt(self): # pragma: no cover
		""" Prompt to complete finished quest and received rewards.
		Should expect answers Y/N.
		"""
		raise NotImplementedError()
	def check(self, game): # pragma: no cover
		""" Should return True is quest condition is fullfilled
		and quest can be completed.
		"""
		raise NotImplementedError()
	def complete(self, game): # pragma: no cover
		""" Should complete quest, give rewards and otherwise affect game world.
		"""
		raise NotImplementedError()
