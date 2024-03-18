import lxml.etree
import contextlib
from . import ConfigFilter, config_filter

@config_filter('xml')
class XMLConfig(ConfigFilter):
	""" XML config. """
	@contextlib.contextmanager
	def AutoDeserialize(self, pretty=False):
		""" Temporarily deserializes XML data into a proper object.
		Provides self.tree for deserialized tree.
		"""
		try:
			self.tree = lxml.etree.fromstring(self.content)
			yield
		finally:
			self.content = lxml.etree.tostring(self.tree, encoding='unicode', pretty_print=pretty)
	def sort(self): # pragma: no cover
		raise NotImplementedError
	def delete(self, pattern, pattern_type=None): # pragma: no cover
		raise NotImplementedError
	def replace(self, pattern, substitute, pattern_type=None): # pragma: no cover
		raise NotImplementedError
	def pretty(self):
		with self.AutoDeserialize(pretty=True):
			pass # No op, just serialize pretty data back.

