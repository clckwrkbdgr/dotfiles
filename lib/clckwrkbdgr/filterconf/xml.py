from __future__ import absolute_import
import time
try: # pragma: no cover
	import lxml.etree as ET
	def _find_abs_xpath(el, xpath):
		elements = el.xpath(xpath)
		for element in elements:
			if isinstance(element, ET._ElementUnicodeResult) or isinstance(element, ET._ElementStringResult) :
				yield element.getparent(), element.attrname
			else:
				yield element, None
	def _getparent(element, root):
		return element.getparent()
	def _prettify(root):
		parser = ET.XMLParser(remove_blank_text=True)
		data = ET.XML(ET.tostring(root), parser=parser)
		return ET.tostring(data, encoding='utf-8', xml_declaration=True, pretty_print=True).decode('utf-8').rstrip() + '\n'
	def _tostring(root):
		return ET.tostring(root, encoding='utf-8', xml_declaration=True).decode('utf-8').rstrip() + '\n'
	ET.FunctionNamespace(None)['current-timestamp'] = lambda dummy: int(time.time())
except ImportError: # pragma: no cover
	import xml.etree.ElementTree as ET
	import xml.dom.minidom
	def _find_abs_xpath(el, xpath):
		assert xpath.startswith('/')
		root_name, rel_xpath = xpath[1:].split('/', 1)
		assert el.tag == root_name
		for element in el.findall("./" + rel_xpath):
			yield element, None # FIXME need to parse attrs
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
		return ET.fromstring(self.content.encode('utf-8'))
	def pack(self, data):
		pretty = hasattr(self, 'do_prettify') and self.do_prettify
		if pretty:
			return _prettify(data)
		return _tostring(data)
	def sort(self, xpath):
		""" Sorts XML nodes in-place at specified xpath/@attr, e.g.: /root/sub/item/@attr.
		"""
		parents = {}
		for sort_item, _attr in _find_abs_xpath(self.content, xpath):
			parents[sort_item.getparent()] = (sort_item.tag, _attr)
		for sort_parent, (sort_item, sort_key) in parents.items():
			sort_parent[:] = sorted(sort_parent, key=lambda child: None if child.tag != sort_item else child.get(sort_key))
	def delete(self, xpath, pattern, pattern_type=None):
		""" Deletes XML nodes at specified xpath (node/attr) matching given pattern.
		E.g. /root/sub/item/@attr - removes ./item where attr matches pattern,
		or /root/sub/item - removes item where content matches pattern.
		"""
		pattern = convert_pattern(pattern, pattern_type)
		for element, attr in _find_abs_xpath(self.content, xpath):
			if attr:
				element_attr = element.get(attr)
				if element_attr and pattern.match(element_attr):
					_getparent(element, self.content).remove(element)
			else:
				if element.text is None or pattern.match(element.text):
					_getparent(element, self.content).remove(element)
	def replace(self, xpath, pattern, substitute, pattern_type=None):
		""" If substitute starts with 'xpath:', the rest of the string is evaluated as XPath expression and result is used as a substitute, e.g.: xpath:count(/root/items/item)
		"""
		if substitute.startswith('xpath:'):
			substitute = str(self.content.xpath(substitute[len('xpath:'):]))
		pattern = convert_pattern(pattern, pattern_type)
		for element, attr in _find_abs_xpath(self.content, xpath):
			if attr:
				element_attr = element.get(attr)
				if element_attr and pattern.match(element_attr):
					element.attrib[attr] = pattern.sub(substitute, element.attrib[attr])
			else:
				if pattern.match(element.text):
					element.text = pattern.sub(substitute, element.text)
	def pretty(self):
		self.do_prettify = True # No op, just serialize pretty data back.
