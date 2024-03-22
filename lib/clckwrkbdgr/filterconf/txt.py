import contextlib
from . import ConfigFilter, config_filter
from . import convert_pattern

@config_filter('txt')
class PlainText(ConfigFilter):
	""" Plain-text config (or unknown format). """
	@contextlib.contextmanager
	def AutoSplitlines(self):
		""" Splits self.content to self.lines and joins them back upon exit.
		Remembers if original text value of attribute ended with newline
		and restores it upon exit.
		"""
		try:
			ends_with_cr = self.content.endswith('\n')
			self.lines = self.content.splitlines()
			yield
		finally:
			self.content = '\n'.join(self.lines)
			if ends_with_cr:
				self.content += '\n'
	def sort(self, _path):
		""" Sorting is performed by lines alphabetically. """
		with self.AutoSplitlines():
			self.lines = sorted(self.lines)
	def delete(self, _path, pattern, pattern_type=None):
		""" Removes lines that contain specified substring/regex/wildcard. """
		pattern = convert_pattern(pattern, pattern_type)
		with self.AutoSplitlines():
			self.lines = [line for line in self.lines if not pattern.search(line)]
	def replace(self, _path, pattern, substitute, pattern_type=None):
		""" Replaces value specified by substring/regex with substitute. """
		pattern = convert_pattern(pattern, pattern_type)
		with self.AutoSplitlines():
			self.lines = [(pattern.sub(substitute, line) if pattern.search(line) else line) for line in self.lines]
	def pretty(self):
		""" Plain text cannot be prettified. """
		if not self.content.endswith('\n'):
			self.content += '\n'
