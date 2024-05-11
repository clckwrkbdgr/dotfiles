import re, fnmatch
import json
from collections import namedtuple
from . import ConfigFilter, config_filter, convert_pattern

@config_filter('prefs_js')
class PrefsJSConfig(ConfigFilter):
	""" Firefox' prefs.js file. """
	Comment = namedtuple('Comment', 'content')
	Empty = namedtuple('Empty', '')
	UserPref = namedtuple('UserPref', 'name value')
	USERPREF = re.compile(r'^user_pref\("([^"]+)", (true|false|-?\d+|".*")\);$')

	def unpack(self, content):
		entries = []
		for line in content.splitlines():
			if not line.strip():
				entries.append(self.Empty())
			elif line.strip().startswith('//'):
				entries.append(self.Comment(line.strip()[2:].lstrip()))
			elif line.strip().startswith('user_pref'):
				m = self.USERPREF.match(line)
				entries.append(self.UserPref(m.group(1), json.loads(m.group(2))))
			else: # pragma: no cover
				raise NotImplementedError('prefs.js: Unknown line: {0}'.format(repr(line)))
		return entries
	def pack(self, data):
		lines = []
		for entry in data:
			if isinstance(entry, self.Comment):
				lines.append('// {0}'.format(entry.content))
			elif isinstance(entry, self.Empty):
				lines.append('')
			else:
				lines.append('user_pref("{0}", {1});'.format(entry.name, json.dumps(entry.value)))
		return '\n'.join(lines) + '\n'
	def sort(self, xpath):
		""" Sorts user_pref entries by name in-place. """
		fixed = []
		current_group = []
		for entry in self.content:
			if isinstance(entry, self.UserPref):
				current_group.append(entry)
				continue
			if current_group:
				fixed.extend(sorted(current_group))
				current_group = []
			fixed.append(entry)
		if current_group:
			fixed.extend(sorted(current_group))
		self.content = fixed
	def delete(self, name, pattern, pattern_type=None):
		""" Deletes user_pref entries by given name (wildcard or full pattern)
		and optional value pattern of specified type. Empty pattern matches everything.
		"""
		pattern = convert_pattern(pattern, pattern_type) if pattern else None
		self.content = [entry for entry in self.content
				if not isinstance(entry, self.UserPref) or not (
					fnmatch.fnmatch(entry.name, name)
					and (
						not pattern
						or pattern.match(entry.value)
						)
					)]
	def replace(self, name, pattern, substitute, pattern_type=None):
		""" Replaces values of user_pref entries by given name (wildcard or full pattern)
		with substitute value (depends on pattern_type).
		"""
		pattern = convert_pattern(pattern, pattern_type)
		fixed = []
		for entry in self.content:
			if not isinstance(entry, self.UserPref):
				fixed.append(entry)
				continue
			if not fnmatch.fnmatch(entry.name, name):
				fixed.append(entry)
				continue
			str_value = str(entry.value) if not isinstance(entry.value, bool) else str(entry.value).lower()
			if not pattern.search(str_value):
				fixed.append(entry)
				continue
			new_value = pattern.sub(substitute, str_value)
			if isinstance(entry.value, bool) and new_value in ('true', 'false'):
				new_value = new_value == 'true'
			elif isinstance(entry.value, int):
				try:
					new_value = int(new_value)
				except:
					pass
			fixed_entry = self.UserPref(entry.name, new_value)
			fixed.append(fixed_entry)
		self.content = fixed
	def pretty(self):
		""" No need to prettify; always pretty. """
		pass
