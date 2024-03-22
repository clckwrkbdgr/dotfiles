import lxml.etree as ET
import contextlib
from . import ConfigFilter, config_filter, convert_pattern

@config_filter('xml')
class XMLConfig(ConfigFilter):
	""" XML config. """
	def unpack(self, content):
		return ET.fromstring(self.content)
	def pack(self, data):
		pretty = hasattr(self, 'do_prettify') and self.do_prettify
		if pretty:
			parser = ET.XMLParser(remove_blank_text=True)
			data = ET.XML(ET.tostring(data), parser=parser)
			return ET.tostring(data, encoding='unicode', pretty_print=True)
		return ET.tostring(data, encoding='unicode')
	def sort(self, xpath):
		""" Sorts XML nodes in-place at specified xpath@attr, e.g.: /root/sub/item@attr.
		"""
		sort_item, sort_key = xpath.split('@')
		sort_parent, sort_item = sort_item.rsplit('/', 1)
		for sort_parent in self.content.xpath(sort_parent):
			sort_parent[:] = sorted(sort_parent, key=lambda child: None if child.tag != sort_item else child.get(sort_key))
	def delete(self, xpath, pattern, pattern_type=None):
		""" Deletes XML nodes at specified xpath (node/attr) matching given pattern.
		E.g. /root/sub/item@attr - removes ./item where attr matches pattern,
		or /root/sub/item - removes item where content matches pattern.
		"""
		attr = None
		if '@' in xpath:
			xpath, attr = xpath.split('@')
		pattern = convert_pattern(pattern, pattern_type)
		for element in self.content.xpath(xpath):
			if attr:
				if pattern.match(element.get(attr)):
					element.getparent().remove(element)
			else:
				if pattern.match(element.text):
					element.getparent().remove(element)
	def replace(self, xpath, pattern, substitute, pattern_type=None):
		attr = None
		if '@' in xpath:
			xpath, attr = xpath.split('@')
		pattern = convert_pattern(pattern, pattern_type)
		for element in self.content.xpath(xpath):
			if attr:
				if pattern.match(element.get(attr)):
					element.attrib[attr] = pattern.sub(substitute, element.attrib[attr])
			else:
				if pattern.match(element.text):
					element.text = pattern.sub(substitute, element.text)
	def pretty(self):
		self.do_prettify = True # No op, just serialize pretty data back.

