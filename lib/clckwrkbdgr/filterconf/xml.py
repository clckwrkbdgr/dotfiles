from __future__ import absolute_import
import time
import six
try: # pragma: no cover
	import lxml.etree as ET
	def _parse(content):
		return ET.fromstring(content.encode('utf-8'))
	def _get_xpath_value(root, xpath):
		return root.xpath(xpath)
	def _find_abs_xpath(el, xpath):
		elements = el.xpath(xpath, namespaces=el.nsmap)
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
	from io import BytesIO, StringIO
	import re
	def _parse(content):
		root = ET.fromstring(content.encode('utf-8'))
		namespaces = dict([
			node for _, node in ET.iterparse(
				StringIO(six.text_type(content)), events=[u'start-ns']
				)
			])
		for name, value in namespaces.items():
			ET.register_namespace(name, value)
			_parse.nsmap[name] = value
		return root
	_parse.nsmap = {} # ET's built-in _namespace_map is backwards, not fit for findall() calls.
	def _get_xpath_value(root, xpath): # Limited support for some XPath features like functions.
		""" Supports only following functions:
		- count(/...)
		- current-timestamp()
		"""
		if xpath.startswith('count('):
			xpath = xpath[len('count('):-1]
			result = float(len(list(_find_abs_xpath(root, xpath))))
			return result
		if xpath == 'current-timestamp()':
			return float(int(time.time()))
		return root.find(xpath)
	XPATH_WITH_ATTR = re.compile(r'^(.*)/@([-A-Za-z_0-9]+)$')
	def _find_abs_xpath(el, xpath):
		assert xpath.startswith('/')
		root_name, rel_xpath = xpath[1:].split('/', 1)
		el_real_tag = el.tag
		if '}' in el_real_tag:
			el_ns, el_real_tag = el_real_tag.split('}')
			el_ns = el_ns.rsplit('/', 1)[-1].rstrip('#')
			el_real_tag = el_ns + ':' + el_real_tag
		assert el_real_tag == root_name
		attr = XPATH_WITH_ATTR.match(rel_xpath)
		if attr:
			rel_xpath, attr = attr.group(1), attr.group(2)
		elif rel_xpath.startswith('@'):
			rel_xpath, attr = None, rel_xpath[1:]
		if not rel_xpath:
			if attr:
				yield el, attr
			else:
				yield el, None
			return
		for element in el.findall("./" + rel_xpath, namespaces=_parse.nsmap):
			if attr:
				yield element, attr
			else:
				yield element, None
	def _getparent(element, root):
		parent_map = dict((c, p) for p in root.iter() for c in p)
		return parent_map[element]
	def _prettify(root):
		result = xml.dom.minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ", encoding='utf-8')
		xml_declaration, result = result.split(b'>', 1)
		result = xml_declaration.replace(b'"', b"'") + b'>' + result
		return result.decode('utf-8')
	def _tostring(root):
		f = BytesIO()
		ET.ElementTree(root).write(f, encoding='utf-8', xml_declaration=True) 
		return f.getvalue().decode('utf-8').replace(' />', '/>').rstrip() + '\n'
import contextlib
from . import ConfigFilter, config_filter, convert_pattern

@config_filter('xml')
class XMLConfig(ConfigFilter):
	""" XML config. """
	def unpack(self, content):
		return _parse(self.content)
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
			parents[_getparent(sort_item, self.content)] = (sort_item.tag, _attr)
		for sort_parent, (sort_item, sort_key) in parents.items():
			sort_parent[:] = sorted(sort_parent, key=lambda child: '' if child.tag != sort_item else child.get(sort_key))
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
			substitute = str(_get_xpath_value(self.content, substitute[len('xpath:'):]))
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
