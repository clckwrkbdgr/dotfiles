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
			filter.pretty()
		self.assertEqual(filter.content, expected)
