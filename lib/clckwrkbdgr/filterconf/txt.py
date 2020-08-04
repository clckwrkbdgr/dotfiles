import re, fnmatch
import contextlib
from . import ConfigFilter, config_filter

def convert_pattern(pattern, pattern_type=None):
	""" Returns compiled regex object. """
	if pattern_type == 'regex':
		return re.compile(pattern)
	elif pattern_type == 'wildcard':
		return re.compile(fnmatch.translate(pattern))
	return re.compile(re.escape(pattern))

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
	def sort(self):
		""" Sorting is performed by lines alphabetically. """
		with self.AutoSplitlines():
			self.lines = sorted(self.lines)
	def delete(self, pattern, pattern_type=None):
		""" Removes lines that contain specified substring/regex/wildcard. """
		pattern = convert_pattern(pattern, pattern_type)
		with self.AutoSplitlines():
			self.lines = [line for line in self.lines if not pattern.search(line)]
	def replace(self, pattern, substitute, pattern_type=None):
		""" Replaces value specified by substring/regex with substitute. """
		pattern = convert_pattern(pattern, pattern_type)
		with self.AutoSplitlines():
			self.lines = [(pattern.sub(substitute, line) if pattern.search(line) else line) for line in self.lines]
	def pretty(self):
		""" Plain text cannot be prettified. """
		if not self.content.endswith('\n'):
			self.content += '\n'
