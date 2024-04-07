from collections import OrderedDict
import re, fnmatch
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

def convert_pattern(pattern, pattern_type=None):
	""" Helper function to handle all pattern types for text replacement.
	Returns compiled regex object.
	"""
	if pattern_type == 'regex':
		return re.compile(pattern)
	elif pattern_type == 'wildcard':
		return re.compile(fnmatch.translate(pattern))
	return re.compile(re.escape(pattern))

class ConfigFilter:
	""" Basic class for config filter.
	Should be created for specific content.
	Supports several actions performed on this content, see ACTIONS in args.
	"""
	def __init__(self, content): # pragma: no cover
		self.content = content
	def __enter__(self):
		self.content = self.unpack(self.content)
		return self
	def __exit__(self, *args, **kwargs):
		self.content = self.pack(self.content)
	@classmethod
	def description(filterclass):
		docs = [
				inspect.getdoc(filterclass),
				inspect.getdoc(filterclass.sort),
				]
		return '\n'.join(docs)
	@classmethod
	def decode(cls, binary_data):
		""" Converts config from binary form to text representation
		suitable to be stored in VCS.
		By default just treats input as UTF-8 text.
		"""
		return binary_data.decode('utf-8')
	@classmethod
	def encode(cls, text_repr):
		""" Converts text representation back to the original binary form.
		By default just encodes output as UTF-8 text.
		"""
		return text_repr.encode('utf-8')
	def unpack(self, content): # pragma: no cover
		""" Should unpack text content into format-dependent data structure.
		It will be available in field .data.
		By default returns text as-is.
		"""
		return content
	def pack(self, data): # pragma: no cover
		""" Should pack working format-dependent data structure back into text content.
		By default returns text as-is.
		"""
		return data
	def sort(self, path): # pragma: no cover
		""" Should sort list of values at provided path. """
		raise NotImplementedError
	def delete(self, path, pattern, pattern_type=None): # pragma: no cover
		""" Should delete values at provided path that match given pattern. """
		raise NotImplementedError
	def replace(self, pattern, substitute, pattern_type=None): # pragma: no cover
		""" Should replace values at provided path that match given pattern with given substitute value. """
		raise NotImplementedError
	def pretty(self): # pragma: no cover
		""" Should prettify result output.
		Default output is allowed to be not pretty.
		"""
		raise NotImplementedError

config_filter = AutoRegistry()
