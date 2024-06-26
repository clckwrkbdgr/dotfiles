import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.xml import XMLConfig

class TestXMLConfig(unittest.TestCase):
	def should_prettify_xml_doc(self):
		content = '<root><item attr1="bar" attr2="foo"/><item attr="foo">foobar</item></root>'
		expected = textwrap.dedent(u"""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <item attr1="bar" attr2="foo"/>
				  <item attr="foo">foobar</item>
				</root>
				""")

		with XMLConfig(content) as filter:
			filter.pretty()
		if filter.content.startswith('<?xml version="1.0" ?>\n'): filter.content = filter.content[len('<?xml version="1.0" ?>\n'):]
		self.assertEqual(filter.content, expected)
	def should_process_xml_with_nsmap(self):
		content = textwrap.dedent("""\
				<MY:root xmlns:MY="http://localhost/nsmap/MY#">
				  <MY:list>
					<MY:item attr="foo"/>
					<MY:item attr="baz"/>
					<MY:item attr="bar"/>
				  </MY:list>
				</MY:root>
				""")
		expected = textwrap.dedent(u"""\
				<?xml version='1.0' encoding='utf-8'?>
				<MY:root xmlns:MY="http://localhost/nsmap/MY#">
				  <MY:list>
				    <MY:item attr="bar"/>
				    <MY:item attr="baz"/>
				    <MY:item attr="foo"/>
				  </MY:list>
				</MY:root>
				""")
		with XMLConfig(content) as filter:
			filter.sort('/MY:root/MY:list/MY:item/@attr')
			filter.pretty()
		if filter.content.startswith('<?xml version="1.0" ?>\n'): filter.content = filter.content[len('<?xml version="1.0" ?>\n'):]
		self.assertEqual('\n'.join(line for line in filter.content.splitlines() if line.strip()) + '\n', expected)
	def should_sort_xml_by_specified_path(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		expected = textwrap.dedent(u"""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <list>
				    <item attr="bar"/>
				    <item attr="baz"/>
				    <item attr="foo"/>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.sort('/root/list/item/@attr')
			filter.pretty()
		if filter.content.startswith('<?xml version="1.0" ?>\n'): filter.content = filter.content[len('<?xml version="1.0" ?>\n'):]
		self.assertEqual('\n'.join(line for line in filter.content.splitlines() if line.strip()) + '\n', expected)
	def should_remove_nodes_by_specified_path_and_pattern_matching_attr(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item>bar</item>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <list>
				    <item attr="baz"/>
				    <item>bar</item>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.delete('/root/list/item/@attr', '.*o$', pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_remove_nodes_by_specified_path_and_pattern_matching_text(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item>foo</item>
				    <item>baz</item>
				    <item>bar</item>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <list>
				    <item>baz</item>
				    <item>bar</item>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.delete('/root/list/item', '.*o$', pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_in_nodes_by_specified_path_and_pattern(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item>bar</item>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <list>
				    <item attr="FOOBAR"/>
				    <item attr="baz"/>
				    <item>bar</item>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.replace('/root/list/item/@attr', '.*o$', 'FOOBAR', pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_in_nodes_by_xpath_search_expression_with_another_attr(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="foo" value="1"/>
				    <item attr="baz" value="2"/>
				    <item>bar</item>
				  </list>
				</root>
				""")
		expected = textwrap.dedent(u"""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <list>
				    <item attr="foo" value="666"/>
				    <item attr="baz" value="2"/>
				    <item>bar</item>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.replace('/root/list/item[@attr="foo"]/@value', '1', '666')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_in_the_root_node(self):
		content = textwrap.dedent("""\
				<?xml version="1.0" encoding="utf-8"?>
				<root bar="1" foo="123456">
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<?xml version='1.0' encoding='utf-8'?>
				<root bar="0" foo="666">
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.replace('/root/@foo', '^.*$', '666', pattern_type='regex')
			filter.replace('/root/@bar', '^.*$', '0', pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_with_xpath_expr_values(self):
		content = textwrap.dedent("""\
				<?xml version="1.0" encoding="utf-8"?>
				<root bar="0" foo="0">
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		expected = textwrap.dedent(u"""\
				<?xml version='1.0' encoding='utf-8'?>
				<root bar="3.0" foo="0">
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.replace('/root/@bar', '0', 'xpath:count(/root/list/item)')
		self.assertEqual(filter.content, expected)
	@unittest.mock.patch('time.time', side_effect=[123456.789])
	def should_replace_attr_values_with_timestamp_using_xpath_expr(self, time_time):
		content = textwrap.dedent("""\
				<?xml version="1.0" encoding="utf-8"?>
				<root bar="0" foo="0">
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		expected = textwrap.dedent(u"""\
				<?xml version='1.0' encoding='utf-8'?>
				<root bar="123456.0" foo="0">
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.replace('/root/@bar', '0', 'xpath:current-timestamp()')
		self.assertEqual(filter.content, expected)
	def should_replace_content_in_nodes_by_specified_path_and_pattern(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item>foo</item>
				    <item>baz</item>
				    <item>bar</item>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<?xml version='1.0' encoding='utf-8'?>
				<root>
				  <list>
				    <item>FOOBAR</item>
				    <item>baz</item>
				    <item>bar</item>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.replace('/root/list/item', '.*o$', 'FOOBAR', pattern_type='regex')
		self.assertEqual(filter.content, expected)
