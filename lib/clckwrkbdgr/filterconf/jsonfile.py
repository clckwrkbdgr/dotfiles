import re, json
import contextlib
import six
from . import ConfigFilter, config_filter

@config_filter('json')
class JSONConfig(ConfigFilter):
	""" JSON config. """
	@contextlib.contextmanager
	def AutoDeserialize(self):
		""" Temporarily deserializes JSON data into a proper object.
		Auto-prettifies output on dumping.
		Provides self.data for deserialized data.
		"""
		try:
			current_indent = 2 if six.PY2 else '\t'
			second_line = self.content.find('\n')
			if second_line > -1:
				second_line += 1
				text_start = re.search(r'[^ \t]+', self.content[second_line:second_line+100])
				if text_start:
					current_indent = self.content[second_line:second_line+text_start.start()]
				if six.PY2: # pragma: no cover
					current_indent = len(current_indent.replace('\t', '  '))

			self.data = json.loads(self.content)
			yield
		finally:
			self.content = json.dumps(self.data,
					ensure_ascii=False,
					indent=current_indent,
					sort_keys=True,
					)
			if not self.content.endswith('\n'):
				self.content += '\n'
	def sort(self):
		""" For JSON, sorting is a part of prettifying.
		Specifically: sorting keys in dictionaries.
		"""
		self.pretty()
	def _navigate(self, path):
		path = path.split('/' if '/' in path else '.')
		value = self.data
		while len(path) > 1:
			key = path.pop(0)
			if not isinstance(value, dict):
				key = int(key)
			value = value[key]
		key = path[0]
		if not isinstance(value, dict):
			key = int(key)
		return value, key
	def delete(self, pattern, pattern_type=None):
		""" Removes item for specified path (sequence of keys separated by dots or slashes).
		Pattern type is ignored.
		"""
		with self.AutoDeserialize():
			obj, key = self._navigate(pattern)
			del obj[key]
	def replace(self, pattern, substitute, pattern_type=None):
		""" Replaces item at specified path with another value.
		Path is treated as for delete().
		"""
		with self.AutoDeserialize():
			obj, key = self._navigate(pattern)
			obj[key] = substitute
	def pretty(self):
		""" Sorting keys, indenting (trying to guess current indent or using TAB).
		"""
		with self.AutoDeserialize():
			pass # No op, just serialize pretty data back.
