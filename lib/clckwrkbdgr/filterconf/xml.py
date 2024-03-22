import lxml.etree
import contextlib
from . import ConfigFilter, config_filter

@config_filter('xml')
class XMLConfig(ConfigFilter):
	""" XML config. """
	def unpack(self, content):
		return lxml.etree.fromstring(self.content)
	def pack(self, data):
		pretty = hasattr(self, 'do_prettify') and self.do_prettify
		return lxml.etree.tostring(data, encoding='unicode', pretty_print=pretty)
	def sort(self, path): # pragma: no cover
		raise NotImplementedError
	def delete(self, path, pattern, pattern_type=None): # pragma: no cover
		raise NotImplementedError
	def replace(self, path, pattern, substitute, pattern_type=None): # pragma: no cover
		raise NotImplementedError
	def pretty(self):
		self.do_prettify = True # No op, just serialize pretty data back.

