from collections import OrderedDict
import inspect
from clckwrkbdgr.collections import AutoRegistry

class Environment(object):
	""" Keeps track of variables which can be used in config substitution.
	See --enviro argument.
	"""
	def __init__(self):
		self.envvars = OrderedDict() # name: value
		self.known_vars = OrderedDict() # name: lambda
	def known_names(self):
		""" Returns list of names of the known variables. """
		return self.known_vars.keys()
	def register(self, name, loader):
		""" Registers new variable with 'loader' function
		which is used to get the value.
		"""
		self.known_vars[name] = loader
	def get(self, name):
		""" Returns value of the specified variable. """
		if name not in self.envvars:
			self.envvars[name] = self.known_vars[name]()
		return self.envvars[name]

class ConfigFilter:
	""" Basic class for config filter.
	Should be created for specific content.
	Supports several actions performed on this content, see ACTIONS in args.
	"""
	def __init__(self, content): # pragma: no cover
		self.content = content
	@classmethod
	def description(filterclass):
		docs = [
				inspect.getdoc(filterclass),
				inspect.getdoc(filterclass.sort),
				]
		return '\n'.join(docs)
	def sort(self): # pragma: no cover
		raise NotImplementedError
	def delete(self, pattern, pattern_type=None): # pragma: no cover
		raise NotImplementedError
	def replace(self, pattern, substitute, pattern_type=None): # pragma: no cover
		raise NotImplementedError
	def pretty(self): # pragma: no cover
		raise NotImplementedError

config_filter = AutoRegistry()

