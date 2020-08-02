import re, fnmatch
from . import ConfigFilter, config_filter

@config_filter('txt')
class PlainText(ConfigFilter):
	""" Plain-text config (or unknown format). """
	def sort(self):
		""" Sorting is performed by lines alphabetically. """
		ends_with_cr = self.content.endswith('\n')
		self.content = '\n'.join(sorted(self.content.splitlines()))
		if ends_with_cr:
			self.content += '\n'
	def delete(self, pattern, pattern_type=None):
		""" Removes lines that contain specified substring/regex/wildcard. """
		ends_with_cr = self.content.endswith('\n')
		lines = self.content.splitlines()

		if pattern_type == 'regex':
			pattern = re.compile(pattern)
		elif pattern_type == 'wildcard':
			pattern = fnmatch.translate(pattern)
		else:
			class DummyPattern:
				def __init__(self, expr):
					self.expr = expr
				def match(self, line):
					return self.expr in line
			pattern = DummyPattern(pattern)

		lines = [line for line in lines if not pattern.match(line)]
		self.content = '\n'.join(lines)
		if ends_with_cr:
			self.content += '\n'
	def replace(self, pattern, substitute, pattern_type=None):
		""" Replaces value specified by substring/regex with substitute. """
		ends_with_cr = self.content.endswith('\n')
		lines = self.content.splitlines()

		if pattern_type == 'regex':
			pattern = re.compile(pattern)
		else:
			class DummyPattern:
				def __init__(self, expr):
					self.expr = expr
				def match(self, line):
					return self.expr in line
				def sub(self, repl, line):
					return line.replace(self.expr, repl)
			pattern = DummyPattern(pattern)
		lines = [(pattern.sub(substitute, line) if pattern.match(line) else line) for line in lines]

		self.content = '\n'.join(lines)
		if ends_with_cr:
			self.content += '\n'
	def pretty(self):
		""" Plain text cannot be prettified. """
		pass
