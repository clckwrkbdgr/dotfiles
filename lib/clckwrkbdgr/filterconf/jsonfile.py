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
		Path should not contain wildcards.

		Supports very limited sortkey conditions:
		- /path/...[key] - sort by subkey
		- /path/...[key1+key2] - sort by compound keys
		"""
		condition = None
		if '[' in path:
			path, condition = path.split('[', 1)
			condition = condition[:-1] # Closing ]
		obj, key = next(self._navigate(path))
		if condition:
			condition = condition.split('+')
			def sortkey(subobj):
				return ''.join(str(subobj.get(subkey, '')) for subkey in condition)
			obj[key] = sorted(obj[key], key=sortkey)
		else:
			obj[key] = sorted(obj[key])
	def _navigate(self, path):
		path = path.split('/' if '/' in path else '.')
		value = self.content
		for result in self._subnavigate(path, value):
			yield result
	def _keys(self, value):
		if isinstance(value, dict):
			return value.keys()
		return range(len(value)) if isinstance(value, list) else []
	def _subnavigate(self, path, value):
		key, path = path[0], path[1:]
		if not isinstance(value, dict) and key != '*':
			key = int(key)
		if not path:
			if key == '*':
				for key in self._keys(value):
					yield value, key
				return
			yield value, key
			return
		if key == '*':
			for key in self._keys(value):
				for result in self._subnavigate(path, value[key]):
					yield result
			return
		for result in self._subnavigate(path, value[key]):
			yield result
	def delete(self, path, pattern, pattern_type=None):
		""" Removes item for specified path (sequence of keys separated by dots or slashes).
		Path can contain wildcards ('*' can match any children node).
		Pattern type is ignored.
		"""
		pattern = convert_pattern(pattern, pattern_type)
		for obj, key in self._navigate(path):
			parent_obj = obj
			if key or isinstance(key, int):
				try:
					obj = obj[key]
				except KeyError:
					continue
			if not isinstance(obj, list) and not isinstance(obj, dict):
				if not (obj is None and pattern.match('null')):
					continue # pragma: no cover -- single continue statement is not covered by py2 coverage.
				del parent_obj[key]
				continue
			for entry in list(obj):
				if pattern.search(str(entry)):
					if isinstance(obj, dict):
						del obj[entry]
					else:
						obj.remove(entry)
	def replace(self, path, pattern, substitute, pattern_type=None):
		""" Replaces item at specified path with another JSON object (e.g. a dict or even a string).
		Path is treated as for delete().
		"""
		pattern = convert_pattern(pattern, pattern_type)
		for obj, key in self._navigate(path):
			if isinstance(obj[key], dict):
				for subkey in obj[key]:
					if pattern.search(subkey):
						obj[key][subkey] = json.loads(substitute)
			else:
				if pattern.search(str(obj[key])):
					obj[key] = json.loads(substitute)
	def pretty(self):
		""" Sorting keys, indenting (trying to guess current indent or using TAB).
		"""
		pass # No op, just serialize pretty data back.

@config_filter('json_mozLz4')
class JSONMozLz4Config(JSONConfig):
	""" JSON config encoded with mozLz4 codec (Mozilla). """
	@classmethod
	def decode(cls, raw_data): # pragma: no cover -- package lz4 may not be accessible
		from .. import firefox
		return firefox.decompress_mozLz4(raw_data).decode('utf-8')
	@classmethod
	def encode(cls, text_data): # pragma: no cover -- package lz4 may not be accessible
		from .. import firefox
		return firefox.compress_mozLz4(text_data.encode('utf-8'))
