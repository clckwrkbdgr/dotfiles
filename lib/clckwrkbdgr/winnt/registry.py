from __future__ import unicode_literals
import io
from collections import namedtuple
import six
import clckwrkbdgr.utils as utils

class BaseRegistryEntry(object):
	def __init__(self):
		self.line_number = 0

class Header(BaseRegistryEntry):
	def __init__(self, value):
		super(Header, self).__init__()
		self.value = value
	def __str__(self):
		return self.value + '\n'
	def __repr__(self): # pragma: no cover
		return '{0}({1})'.format(type(self).__name__, repr(self.value))
	def __eq__(self, other):
		return type(self) == type(other) and self.value == other.value

class EmptyLine(BaseRegistryEntry):
	def __str__(self):
		return '\n'
	def __repr__(self): # pragma: no cover
		return '{0}()'.format(type(self).__name__)
	def __eq__(self, other):
		return type(self) == type(other)

class Key(BaseRegistryEntry):
	def __init__(self, *path):
		super(Key, self).__init__()
		if len(path) == 1 and utils.is_collection(path[0]):
			self.path = tuple(path[0])
		else:
			self.path = tuple(path)
	def __str__(self):
		return '[{0}]\n'.format('\\'.join(self.path))
	def __repr__(self): # pragma: no cover
		return '{0}{1}'.format(type(self).__name__, repr(self.path))
	def __eq__(self, other):
		return type(self) == type(other) and self.path == other.path

class DefaultValueName(object):
	def __str__(self):
		return '@'
	def __repr__(self): # pragma: no cover
		return '@'
	def __eq__(self, other):
		return type(self) == type(other)

def prepare_value_name(name):
	if isinstance(name, DefaultValueName):
		return '@'
	return utils.quote_string(name.replace('\\', '\\\\'))

class Value(BaseRegistryEntry):
	def __init__(self):
		super(Value, self).__init__()

class StringValue(Value):
	def __init__(self, name, value):
		super(StringValue, self).__init__()
		self.name = name
		self.value = value
	def __str__(self):
		return '{0}={1}\n'.format(prepare_value_name(self.name), utils.quote_string(self.value.replace('\\', '\\\\')))
	def __repr__(self): # pragma: no cover
		return '{0}({1}={2})'.format(type(self).__name__, repr(self.name), repr(self.value))
	def __eq__(self, other):
		return type(self) == type(other) and self.name == other.name and self.value == other.value

class DwordValue(Value):
	def __init__(self, name, value):
		super(DwordValue, self).__init__()
		self.name = name
		self.value = value
	def __str__(self):
		return '{0}=dword:{1}\n'.format(prepare_value_name(self.name), ("%0.8X" % self.value).lower())
	def __repr__(self): # pragma: no cover
		return '{0}({1}={2})'.format(type(self).__name__, repr(self.name), repr(self.value))
	def __eq__(self, other):
		return type(self) == type(other) and self.name == other.name and self.value == other.value

class HexValue(Value):
	def __init__(self, name, hex_type, value):
		""" hex_type is a single char or None:
		None : "Value B"=hex:<Binary data (as comma-delimited list of hexadecimal values)>
		0 : "Value D"=hex(0):<REG_NONE (as comma-delimited list of hexadecimal values)>
		1 : "Value E"=hex(1):<REG_SZ (as comma-delimited list of hexadecimal values representing a UTF-16LE NUL-terminated string)>
		2 : "Value F"=hex(2):<Expandable string value data (as comma-delimited list of hexadecimal values representing a UTF-16LE NUL-terminated string)>
		3 : "Value G"=hex(3):<Binary data (as comma-delimited list of hexadecimal values)> ; equal to "Value B"
		4 : "Value H"=hex(4):<DWORD value (as comma-delimited list of 4 hexadecimal values, in little endian byte order)>
		5 : "Value I"=hex(5):<DWORD value (as comma-delimited list of 4 hexadecimal values, in big endian byte order)>
		7 : "Value J"=hex(7):<Multi-string value data (as comma-delimited list of hexadecimal values representing UTF-16LE NUL-terminated strings)>
		8 : "Value K"=hex(8):<REG_RESOURCE_LIST (as comma-delimited list of hexadecimal values)>
		a : "Value L"=hex(a):<REG_RESOURCE_REQUIREMENTS_LIST (as comma-delimited list of hexadecimal values)>
		b : "Value M"=hex(b):<QWORD value (as comma-delimited list of 8 hexadecimal values, in little endian byte order)>
		200000 : ????
		"""
		super(HexValue, self).__init__()
		self.name = name
		self.hex_type = hex_type
		self.value = value
	def __str__(self):
		result = ''
		line = prepare_value_name(self.name)
		line += '=hex{0}:'.format('' if self.hex_type is None else '({0})'.format(self.hex_type))
		first_character_passed = False
		for b in self.value:
			if six.PY2: # pragma: no cover -- py2 only
				b = ("%0.2X," % ord(b)).lower()
			else: # pragma: no cover -- py3 only
				b = ("%0.2X," % b).lower()
			if first_character_passed and len(line) + len(b) > 79:
				result += line + '\\\n'
				line = '  '
			line += b
			first_character_passed = True
		line = line.rstrip(',')
		result += line
		result += '\n'
		return result
	def __repr__(self): # pragma: no cover
		return '{0}({1}=({2}){3})'.format(type(self).__name__, repr(self.name), self.hex_type, repr(self.value))
	def __eq__(self, other):
		return type(self) == type(other) and self.name == other.name and self.value == other.value

def _consume_until_quote(line, fobj, line_number):
	assert line[0] == '"', repr(line)
	result = ''
	line = line[1:]

	while line:
		escape = False
		found = False
		while line:
			c, line = line[0], line[1:]
			if escape:
				result += c
				escape = False
				continue
			if c == '\\':
				escape = True
				continue
			if c == '"':
				found = True
				break
			result += c
		if found:
			break
		else:
			line = fobj.readline()
			line_number += 1
	return result, line, line_number

def fparse(fobj): # TODO PEG grammar (if it is possible to load-on-demand instead of reading full hundreds of MBytes into memory).
	""" Yields parsed entries.
	If with_line_numbers = True, yields pairs (<line number>, <parsed entry>)
	Line numbers start with 1.
	"""
	def return_value(ln, e):
		e.line_number = ln
		return e

	current_key = None
	line_number = 1
	line = fobj.readline()
	assert line.startswith('Windows Registry Editor'), repr(line_number) + repr(line)
	yield return_value(line_number, Header(line.rstrip('\n')))

	while line:
		line_number += 1
		line = fobj.readline()
		if not line:
			break
		if not line.strip():
			yield return_value(line_number, EmptyLine())
			continue
		if line.startswith('['):
			assert line.endswith(']\n'), repr(line_number) + repr(line)
			current_key = line[1:-2].split('\\')
			yield return_value(line_number, Key(current_key))
			continue
		name = None
		new_line_number = line_number
		if line.startswith('@='):
			name = DefaultValueName()
			line = line[2:]
		elif line.startswith('"'):
			name, line, new_line_number = _consume_until_quote(line, fobj, line_number)
			assert line.startswith('='), repr(line_number) + repr(line)
			line = line[1:]

		if not name: # pragma: no cover -- TODO proper exception
			assert False, repr(line_number) + ': Cannot parse line: {0}'.format(repr(line))

		if line.startswith('dword:'):
			value = int(line.split(':', 1)[1], 16)
			yield return_value(line_number, DwordValue(name, value))
			line_number = new_line_number
			continue
		if line.startswith('hex:') or line.startswith('hex('):
			hex_type, value = line.split(':', 1)
			if hex_type == 'hex':
				hex_type = None
			else:
				hex_type = hex_type[3:].lstrip('(').rstrip(')')
			new_line_number = line_number
			while value.endswith(',\\\n'):
				value = value[:-2]
				new_line_number += 1
				new_line = fobj.readline()
				if not new_line: # pragma: no cover -- TODO why?
					break
				value += new_line
			if value.strip():
				if six.PY2: # pragma: no cover -- py2 only
					value = bytes(b''.join(chr(int(b.strip(), 16)) for b in value.split(',')))
				else: # pragma: no cover -- py3 only
					value = bytes(int(b.strip(), 16) for b in value.split(','))
			else:
				value = b''
			yield return_value(line_number, HexValue(name, hex_type, value))
			line_number = new_line_number
			continue
		value, line, new_line_number = _consume_until_quote(line, fobj, line_number)
		assert line == '\n', repr(line_number) + repr(line)
		yield return_value(line_number, StringValue(name, value))
		line_number = new_line_number

def parse(filename): # pragma: no cover -- TODO probably should
	try:
		with open(str(filename), 'r', encoding='utf-16', errors='replace') as f:
			for _ in fparse(f):
				yield _
	except UnicodeError:
		with open(str(filename), 'r', encoding='utf-8', errors='replace') as f:
			for _ in fparse(f):
				yield _

def parse_string(data):
	with io.StringIO(data) as f:
		for _ in fparse(f):
			yield _

def sort(registry_file_entries): # pragma: no cover -- TODO no time now, but should cover it.
	""" Sorts values within keys.
	Yields sorted entries.
	"""
	values = []
	for entry in registry_file_entries:
		if isinstance(entry, Value):
			values.append(entry)
			continue
		if values:
			for _ in sorted(values, key=lambda v: str(v.name)):
				yield _
			values = []
		yield entry
	if values:
		for _ in sorted(values, key=lambda v: str(v.name)):
			yield _
		values = []

def iterate_with_context(registry_file_entries):
	""" Yields pair (<context>, <entry>),
	where current context points to the path of current subkey (+ reg value if present),
	or None if context cannot be determined (yet).
	"""
	current_key = None
	for entry in registry_file_entries:
		context = current_key
		if isinstance(entry, Key):
			current_key = entry.path
			context = current_key
		elif isinstance(entry, Value):
			context = current_key + (str(entry.name),)
		yield context, entry
