from __future__ import unicode_literals
from clckwrkbdgr import unittest
import textwrap, io
import itertools
import clckwrkbdgr.winnt.registry as registry
from clckwrkbdgr.winnt.registry import Header, EmptyLine, Key, Value, StringValue, DwordValue, HexValue, DefaultValueName

class TestUtils(unittest.TestCase):
	def should_consume_name_until_quote(self):
		fobj = io.StringIO('"Test"="Value"')
		line = fobj.readline()
		self.assertEqual(registry._consume_until_quote(line, fobj, 1), ('Test', '="Value"', 1))
	def should_consume_value_until_quote(self):
		fobj = io.StringIO('"Test"="Value"\n')
		line = fobj.readline().split('=', 1)[1]
		self.assertEqual(registry._consume_until_quote(line, fobj, 1), ('Value', '\n', 1))
	def should_consume_multiline_value(self):
		fobj = io.StringIO('"Test"="Value\non\nseveral\nlines"\n')
		line = fobj.readline().split('=', 1)[1]
		self.assertEqual(registry._consume_until_quote(line, fobj, 1), ('Value\non\nseveral\nlines', '\n', 4))
	def should_consume_value_with_escaped_quotes(self):
		fobj = io.StringIO(r'"Test"="Value\\ with \"escaped\" part"' + '\n')
		line = fobj.readline().split('=', 1)[1]
		self.assertEqual(registry._consume_until_quote(line, fobj, 1), ('Value\\ with "escaped" part', '\n', 1))

class TestWindowsRegistryParser(unittest.TestCase):
	def should_parse_reg_file(self):
		data = textwrap.dedent(r"""
		Windows Registry Editor Version 5.00

		[HKEY_CURRENT_USER]

		[HKEY_CURRENT_USER\RegKey]

		[HKEY_CURRENT_USER\RegKey\SubKey]
		@="Default Value"
		"Name"="Value"
		"""[1:])
		entries = list(registry.parse_string(data))
		self.assertEqual(entries, [
			Header('Windows Registry Editor Version 5.00'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER', 'RegKey'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER', 'RegKey', 'SubKey'),
			StringValue(DefaultValueName(), 'Default Value'),
			StringValue('Name', 'Value'),
			])
	def should_parse_values_of_different_types(self):
		data = textwrap.dedent(r"""
		Windows Registry Editor Version 5.00

		[HKEY_CURRENT_USER\RegKey\SubKey]
		@=hex:01
		"String"="Value"
		"Dword"=dword:0001
		"Hex"=hex:01,0A,65
		"Hex2"=hex(2):01,0A,65,\
		  AA,BB,CC,\
		  00,22,33
		"HexEmpty"=hex(0):
		"""[1:])
		entries = list(registry.parse_string(data))
		self.assertEqual(entries, [
			Header('Windows Registry Editor Version 5.00'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER', 'RegKey', 'SubKey'),
			HexValue(DefaultValueName(), None, b'\x01'),
			StringValue('String', 'Value'),
			DwordValue('Dword', int('0001', 16)),
			HexValue('Hex', None, b'\x01\x0a\x65'),
			HexValue('Hex2', '2', b'\x01\x0a\x65\xaa\xbb\xcc\x00\x22\x33'),
			HexValue('HexEmpty', '0', b''),
			])
	def should_convert_parsed_entries_back_to_text(self):
		self.maxDiff = None
		data = textwrap.dedent(r"""
		Windows Registry Editor Version 5.00

		[HKEY_CURRENT_USER\RegKey]

		[HKEY_CURRENT_USER\RegKey\SubKey [With bracketed value]]
		@="Default Value"
		"String"="Value"
		"@"="Not a default Value!"
		"Name\\With\\Escapes"="Value\\With\\Escapes"
		"Dword"=dword:000f0001
		"Hex"=hex:01,0a,65
		"Hex2"=hex(2):01,0a,65
		"Hex20000"=hex(20000):01,0a,65
		"HexMultiline"=hex(2):25,00,53,00,79,00,73,00,74,00,65,00,6d,00,52,00,6f,00,6f,\
		  00,74,00,25,00,5c,00,6d,00,65,00,64,00,69,00,61,00,5c,00,57,00,69,00,6e,00,\
		  64,00,6f,00,77,00,73,00,20,00,42,00,61,00,63,00,6b,00,67,00,72,00,6f,00,75,\
		  00,6e,00,64,00,2e,00,77,00,61,00,76,00,00,00
		"HexMultilineValueTooLongTo_Fit_80_Symbols_limit because Microsoft Regedit does the same"=hex(2):25,\
		  00,74,00,25,00,5c,00,6d,00,65,00,64,00,69,00,61,00,5c,00,57,00,69,00,6e,00
		"""[1:])
		entries = list(registry.parse_string(data))
		self.assertEqual(''.join(map(str, entries)), data)
	def should_number_parsed_entries(self):
		self.maxDiff = None
		data = textwrap.dedent(r"""
		Windows Registry Editor Version 5.00

		[HKEY_CURRENT_USER\RegKey\SubKey]
		@=hex:01
		"String"="Value
		   with
			several
			lines
			"
		"Dword"=dword:0001
		"Hex"=hex:01,0A,65
		"Hex2"=hex(2):01,0A,65,\
		  AA,BB,CC,\
		  00,22,33
		"HexEmpty"=hex(0):
		"""[1:])
		entries = list(registry.parse_string(data))
		entries = list(itertools.chain.from_iterable( (entry.line_number, entry) for entry in entries))
		self.assertEqual(entries, [
			1, Header('Windows Registry Editor Version 5.00'),
			2, EmptyLine(),
			3, Key('HKEY_CURRENT_USER', 'RegKey', 'SubKey'),
			4, HexValue(DefaultValueName(), None, b'\x01'),
			5, StringValue('String', 'Value\n   with\n\tseveral\n\tlines\n\t'),
			10, DwordValue('Dword', int('0001', 16)),
			11, HexValue('Hex', None, b'\x01\x0a\x65'),
			12, HexValue('Hex2', '2', b'\x01\x0a\x65\xaa\xbb\xcc\x00\x22\x33'),
			15, HexValue('HexEmpty', '0', b''),
			])

class TestRegistryProcessor(unittest.TestCase):
	def should_iterate_with_context(self):
		self.maxDiff = None
		entries = [
			Header('Windows Registry Editor Version 5.00'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER', 'RegKey'),
			EmptyLine(),
			Key('HKEY_CURRENT_USER', 'RegKey', 'SubKey'),
			StringValue(DefaultValueName(), 'Default Value'),
			StringValue('Name', 'Value'),
			]
		expected_context = [
			None,
			None,
			('HKEY_CURRENT_USER',),
			('HKEY_CURRENT_USER',),
			('HKEY_CURRENT_USER', 'RegKey'),
			('HKEY_CURRENT_USER', 'RegKey'),
			('HKEY_CURRENT_USER', 'RegKey', 'SubKey'),
			('HKEY_CURRENT_USER', 'RegKey', 'SubKey', '@'),
			('HKEY_CURRENT_USER', 'RegKey', 'SubKey', 'Name'),
			]
		self.assertEqual(
				list(registry.iterate_with_context(entries)),
				list(zip(expected_context, entries)),
				)
