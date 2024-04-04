import six
import collections
try:
	import ConfigParser as configparser
except ImportError: # pragma: no cover
	import configparser
from . import ConfigFilter, config_filter, convert_pattern

@config_filter('ini')
class IniConfig(ConfigFilter):
	""" INI file. """
	def unpack(self, content):
		config = configparser.ConfigParser()
		if hasattr(config, 'read_string'): # pragma: no cover -- py3
			config.read_string(content)
		else: # pragma: no cover -- py2
			stream = six.StringIO(content)
			config.readfp(stream)
		return config
	def pack(self, config):
		stream = six.StringIO()
		if hasattr(config, 'read_string'): # pragma: no cover -- py3
			config.write(stream, space_around_delimiters=True)
		else: # pragma: no cover -- py2
			config.write(stream)
		return stream.getvalue()
	def sort(self, section):
		""" Sorts either specified section or all sections. """
		if section:
			self.content._sections[section] = collections.OrderedDict(sorted(self.content._sections[section].items(), key=lambda t: t[0]))
		else:
			for section in self.content.sections():
				self.content._sections[section] = collections.OrderedDict(sorted(self.content._sections[section].items(), key=lambda t: t[0]))
			self.content._sections = collections.OrderedDict(sorted(self.content._sections.items(), key=lambda t: t[0] ))
	def delete(self, name, pattern, pattern_type=None):
		""" Deletes given value ("section/key") or the whole section ("section").
		If optional pattern is given, deletes only values that match pattern.
		"""
		if '/' in name:
			section, key = name.split('/', 1)
		else:
			section, key = name, None
		if key is None:
			self.content.remove_section(section)
		else:
			pattern = convert_pattern(pattern, pattern_type) if pattern else None
			value = self.content.get(section, key)
			if pattern is None or pattern.match(value):
				self.content.remove_option(section, key)
	def replace(self, name, pattern, substitute, pattern_type=None):
		""" Replaces value in specified key ("section/key") with given substitute.
		"""
		pattern = convert_pattern(pattern, pattern_type)
		section, key = name.split('/', 1)
		self.content.set(section, key, pattern.sub(substitute, self.content.get(section, key)))
	def pretty(self):
		""" No need to prettify; always pretty. """
		pass
