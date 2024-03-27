from __future__ import absolute_import
try: # pragma: no cover
	import lxml.etree as ET
	def _find_abs_xpath(el, xpath):
		return el.xpath(xpath)
	def _getparent(element, root):
		return element.getparent()
	def _prettify(root):
		parser = ET.XMLParser(remove_blank_text=True)
		data = ET.XML(ET.tostring(root), parser=parser)
		return ET.tostring(data, encoding='unicode', pretty_print=True).rstrip() + '\n'
	def _tostring(root):
		return ET.tostring(root, encoding='unicode').rstrip() + '\n'
except ImportError: # pragma: no cover
	import xml.etree.ElementTree as ET
	import xml.dom.minidom
	def _find_abs_xpath(el, xpath):
		assert xpath.startswith('/')
		root_name, rel_xpath = xpath[1:].split('/', 1)
		assert el.tag == root_name
		return el.findall("./" + rel_xpath)
	def _getparent(element, root):
		parent_map = dict((c, p) for p in root.iter() for c in p)
		return parent_map[element]
	def _prettify(root):
		return xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
	def _tostring(root):
		try:
			return ET.tostring(root, encoding='unicode').replace(' />', '/>').rstrip() + '\n'
		except LookupError: # pragma: no cover
			return ET.tostring(root, encoding='utf-8').replace(' />', '/>').rstrip() + '\n'
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
			return _prettify(data)
		return _tostring(data)
	def sort(self, xpath):
		""" Sorts XML nodes in-place at specified xpath@attr, e.g.: /root/sub/item@attr.
		"""
		sort_item, sort_key = xpath.split('@')
		sort_parent, sort_item = sort_item.rsplit('/', 1)
		for sort_parent in _find_abs_xpath(self.content, sort_parent):
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
		for element in _find_abs_xpath(self.content, xpath):
			if attr:
				if pattern.match(element.get(attr)):
					_getparent(element, self.content).remove(element)
			else:
				if pattern.match(element.text):
					_getparent(element, self.content).remove(element)
	def replace(self, xpath, pattern, substitute, pattern_type=None):
		attr = None
		if '@' in xpath:
			xpath, attr = xpath.split('@')
		pattern = convert_pattern(pattern, pattern_type)
		for element in _find_abs_xpath(self.content, xpath):
			if attr:
				if pattern.match(element.get(attr)):
					element.attrib[attr] = pattern.sub(substitute, element.attrib[attr])
			else:
				if pattern.match(element.text):
					element.text = pattern.sub(substitute, element.text)
	def pretty(self):
		self.do_prettify = True # No op, just serialize pretty data back.
