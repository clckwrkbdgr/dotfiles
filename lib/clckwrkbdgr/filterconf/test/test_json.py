import textwrap
import six
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.jsonfile import JSONConfig, JSONMozLz4Config
try:
	import lz4.block
except ImportError: # pragma: no cover
	lz4 = None

class TestJSONConfig(unittest.TestCase):
	def should_sort_json(self):
		content = '{"foo":["value","1"],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"1",
						"value"
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(content) as filter:
			filter.sort("foo")
		self.assertEqual(filter.content, expected)
	def should_sort_json_by_compound_condition(self):
		content = '{"root":[{"location":"b","id":2},{"location":"a","id":2},{"location":"a","id":1}]}'
		expected = textwrap.dedent("""\
				{
					"root": [
						{
							"id": 1,
							"location": "a"
						},
						{
							"id": 2,
							"location": "a"
						},
						{
							"id": 2,
							"location": "b"
						}
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(content) as filter:
			filter.sort("root[location+id]")
		self.assertEqual(filter.content, expected)
	def should_prettify_json(self):
		content = '{"foo":["value","1"],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						"1"
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(content) as filter:
			filter.pretty()
		self.assertEqual(filter.content, expected)
	def should_reindent_using_existing_indent(self):
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"1",
						"value"
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')
		with JSONConfig(expected) as filter:
			filter.sort("foo")
		self.assertEqual(filter.content, expected)
	def should_delete_keys_by_path(self):
		content = '{"foo":["value",1],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"foo": [
						"value",
						1
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("", "bar")
		self.assertEqual(filter.content, expected)

		content = '{"foo":["value",["sublist", 1]],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						[
							1
						]
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("foo.1", "sublist")
		self.assertEqual(filter.content, expected)
	def should_delete_keys_by_path_full_of_wildcards(self):
		content = '{"root":{"foo":{"value":1,"to_delete":true},"bar":{"value":2}},"another-root":{"baz":{"value":3}}}'
		expected = textwrap.dedent("""\
				{
					"another-root": {
						"baz": {
							"value": 3
						}
					},
					"root": {
						"bar": {
							"value": 2
						},
						"foo": {
							"value": 1
						}
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("*.*", "to_delete")
		self.assertEqual(filter.content, expected)
	def should_delete_keys_by_path_with_wildcards_in_dict(self):
		content = '{"root":{"foo":{"value":1,"to_delete":true},"bar":{"value":2}},"another-root":{"foo":{"value":3,"to_delete":true}}}'
		expected = textwrap.dedent("""\
				{
					"another-root": {
						"foo": {
							"value": 3
						}
					},
					"root": {
						"bar": {
							"value": 2
						},
						"foo": {
							"value": 1
						}
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("*.foo", "to_delete")
		self.assertEqual(filter.content, expected)
	def should_delete_keys_by_path_with_wildcards_in_list(self):
		content = '[{"foo":{"value":1,"to_delete":true},"bar":{"value":2}},{"foo":{"value":3,"to_delete":true}}]'
		expected = textwrap.dedent("""\
				[
					{
						"bar": {
							"value": 2
						},
						"foo": {
							"value": 1
						}
					},
					{
						"foo": {
							"value": 3
						}
					}
				]
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("*.foo", "to_delete")
		self.assertEqual(filter.content, expected)
	def should_delete_objects_in_list_by_path_with_wildcards_and_condition(self):
		content = '{"root":[{"name":"foo","value":1,"to_delete":false},{"name":"bar","value":2},{"name":"baz","value":3,"to_delete":true}]}'
		expected = textwrap.dedent("""\
				{
					"root": [
						{
							"name": "foo",
							"to_delete": false,
							"value": 1
						},
						{
							"name": "bar",
							"value": 2
						}
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("root", r"to_delete':\s*True", pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_delete_keys_by_path_with_wildcards_as_keys(self):
		content = '{"root":{"foo":{"value":1,"to_delete":true},"bar":{"value":2},"baz":{"value":3,"to_delete":true},"foobar":[false]}}'
		expected = textwrap.dedent("""\
				{
					"root": {
						"bar": {
							"value": 2
						},
						"baz": {
							"value": 3
						},
						"foo": {
							"value": 1
						},
						"foobar": [
							false
						]
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("root.*", "to_delete")
		self.assertEqual(filter.content, expected)
	def should_delete_keys_with_null_values(self):
		content = '{"root":{"foo":{"value":null,"to_delete":true},"bar":{"value":"str"},"baz":{"value":null,"to_delete":true}}}'
		expected = textwrap.dedent("""\
				{
					"root": {
						"bar": {
							"value": "str"
						},
						"baz": {
							"to_delete": true
						},
						"foo": {
							"to_delete": true
						}
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("*.*.value", "null")
		self.assertEqual(filter.content, expected)
	def should_ignore_wildcards_pointing_to_missing_keys(self):
		content = '{"root":{"foo":{"value":1,"to_delete":true},"bar":{"value":2},"baz":{"value":3,"to_delete":true},"foobar":[false]}}'
		expected = textwrap.dedent("""\
				{
					"root": {
						"bar": {
							"value": 2
						},
						"baz": {
							"to_delete": true,
							"value": 3
						},
						"foo": {
							"to_delete": true,
							"value": 1
						},
						"foobar": [
							false
						]
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("root.foobar.*", "to_delete")
		self.assertEqual(filter.content, expected)
	def should_address_list_elements_by_wildcards(self):
		content = '{"root":[{"foo":1,"baz":true},{"bar":2,"baz":false},{"foo":3}]}'
		expected = textwrap.dedent("""\
				{
					"root": [
						{
							"baz": true
						},
						{
							"baz": false
						},
						{}
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.delete("root/*", "foo")
			filter.delete("root/*", "bar")
		self.assertEqual(filter.content, expected)
	def should_replace_values_by_path(self):
		content = '{"foo":["value",1],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "foobar",
					"foo": [
						"value",
						1
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.replace("bar", "baz", '"foobar"')
		self.assertEqual(filter.content, expected)

		content = '{"foo":["value",["sublist", 1]],"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": [
						"value",
						[
							[
								"fixed_sublist"
							],
							1
						]
					]
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.replace("foo.1.0", "sublist", '["fixed_sublist"]')
		self.assertEqual(filter.content, expected)

		content = '{"foo":{"bar":{"value":1},"baz":2}}'
		expected = textwrap.dedent("""\
				{
					"foo": {
						"bar": {
							"value": {}
						},
						"baz": 2
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.replace("*.bar", "value", '{}')
		self.assertEqual(filter.content, expected)
	def should_replace_int_values(self):
		content = '{"foo":{"value":1},"bar":"baz"}'
		expected = textwrap.dedent("""\
				{
					"bar": "baz",
					"foo": {
						"value": 2
					}
				}
				""")
		if six.PY2: # pragma: no cover
			expected = expected.replace('\t', ' '*2).replace(',\n', ', \n')

		with JSONConfig(content) as filter:
			filter.replace("foo/value", "1", '2')
		self.assertEqual(filter.content, expected)

class TestJSONMozLz4Config(unittest.TestCase):
	@unittest.skipUnless(lz4, 'lz4.block is not detected.')
	def should_decode_mozlz4_json(self): # pragma: no cover -- package lz4 may not be accessible
		self.assertEqual(
				JSONMozLz4Config.decode(b'mozLz40\0\r\0\0\0\xd0{"foo":"bar"}'),
				'{"foo":"bar"}',
				)
	@unittest.skipUnless(lz4, 'lz4.block is not detected.')
	def should_encode_mozlz4_json(self): # pragma: no cover -- package lz4 may not be accessible
		self.assertEqual(
				JSONMozLz4Config.encode('{"foo":"bar"}'),
				b'mozLz40\0\r\0\0\0\xd0{"foo":"bar"}',
				)
