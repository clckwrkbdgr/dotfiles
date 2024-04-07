import re, json
import contextlib
import six
from . import ConfigFilter, config_filter
from . import convert_pattern

@config_filter('json')
class JSONConfig(ConfigFilter):
	""" JSON config. """
	def unpack(self, content):
		self.current_indent = 2 if six.PY2 else '\t'
		second_line = content.find('\n')
		if second_line > -1:
			second_line += 1
			text_start = re.search(r'[^ \t]+', content[second_line:second_line+100])
			if text_start:
				self.current_indent = content[second_line:second_line+text_start.start()]
			if six.PY2: # pragma: no cover
				self.current_indent = len(self.current_indent.replace('\t', '  '))
		return json.loads(content)
	def pack(self, data):
		content = json.dumps(data,
				ensure_ascii=False,
				indent=self.current_indent,
				sort_keys=True,
				)
		if not content.endswith('\n'):
			content += '\n'
		return content
	def sort(self, path):
		""" For JSON, sorting is a part of prettifying.
		Specifically: sorting keys in dictionaries.
		"""
		obj, key = self._navigate(path)
		obj[key] = sorted(obj[key])
	def _navigate(self, path):
		path = path.split('/' if '/' in path else '.')
		value = self.content
		while len(path) > 1:
			key = path.pop(0)
			if not isinstance(value, dict):
				key = int(key)
			value = value[key]
		key = path[0]
		if not isinstance(value, dict):
			key = int(key)
		return value, key
	def delete(self, path, pattern, pattern_type=None):
		""" Removes item for specified path (sequence of keys separated by dots or slashes).
		Pattern type is ignored.
		"""
		pattern = convert_pattern(pattern, pattern_type)
		obj, key = self._navigate(path)
		if key:
			obj = obj[key]
		for entry in list(obj):
			if pattern.search(str(entry)):
				if isinstance(obj, dict):
					del obj[entry]
				else:
					obj.remove(entry)
	def replace(self, path, pattern, substitute, pattern_type=None):
		""" Replaces item at specified path with another value.
		Path is treated as for delete().
		"""
		pattern = convert_pattern(pattern, pattern_type)
		obj, key = self._navigate(path)
		if pattern.search(obj[key]):
			obj[key] = substitute
	def pretty(self):
		""" Sorting keys, indenting (trying to guess current indent or using TAB).
		"""
		pass # No op, just serialize pretty data back.

@config_filter('json_mozLz4')
class JSONMozLz4Config(ConfigFilter):
	""" JSON config encoded with mozLz4 codec (Mozilla). """
	@classmethod
	def decode(cls, raw_data):
		from .. import firefox
		return firefox.decompress_mozLz4(raw_data).decode('utf-8')
	@classmethod
	def encode(cls, text_data):
		from .. import firefox
		return firefox.compress_mozLz4(text_data.encode('utf-8'))
