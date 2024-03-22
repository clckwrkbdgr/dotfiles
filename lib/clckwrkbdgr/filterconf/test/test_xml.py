import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.xml import XMLConfig

class TestXMLConfig(unittest.TestCase):
	def should_prettify_xml_doc(self):
		content = '<root><item attr2="foo" attr1="bar"/><item attr="foo">foobar</item></root>'
		expected = textwrap.dedent("""\
				<root>
				  <item attr2="foo" attr1="bar"/>
				  <item attr="foo">foobar</item>
				</root>
				""")

		with XMLConfig(content) as filter:
			pass # Not pretty.
		self.assertEqual(filter.content, content)

		with XMLConfig(content) as filter:
			filter.pretty()
		self.assertEqual(filter.content, expected)
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
		expected = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="bar"/>
				    <item attr="baz"/>
				    <item attr="foo"/>
				  </list>
				</root>
				""")
		with XMLConfig(content) as filter:
			filter.sort('/root/list/item@attr')
			filter.pretty()
		self.assertEqual(filter.content, expected)
	def should_remove_nodes_by_specified_path_and_pattern_matching_attr(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>""")
		with XMLConfig(content) as filter:
			filter.delete('/root/list/item@attr', '.*o$', pattern_type='regex')
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
				<root>
				  <list>
				    <item>baz</item>
				    <item>bar</item>
				  </list>
				</root>""")
		with XMLConfig(content) as filter:
			filter.delete('/root/list/item', '.*o$', pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_replace_attr_values_in_nodes_by_specified_path_and_pattern(self):
		content = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="foo"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>
				""")
		expected = textwrap.dedent("""\
				<root>
				  <list>
				    <item attr="FOOBAR"/>
				    <item attr="baz"/>
				    <item attr="bar"/>
				  </list>
				</root>""")
		with XMLConfig(content) as filter:
			filter.replace('/root/list/item@attr', '.*o$', 'FOOBAR', pattern_type='regex')
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
				<root>
				  <list>
				    <item>FOOBAR</item>
				    <item>baz</item>
				    <item>bar</item>
				  </list>
				</root>""")
		with XMLConfig(content) as filter:
			filter.replace('/root/list/item', '.*o$', 'FOOBAR', pattern_type='regex')
		self.assertEqual(filter.content, expected)
