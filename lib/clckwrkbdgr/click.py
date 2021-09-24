from __future__ import absolute_import
import click
import six
if six.PY2: # pragma: no cover
	from click import *

""" Custom extensions for click CLI API. """

class RawEpilogGroup(click.Group): # pragma: no cover
	def format_epilog(self, ctx, formatter):
		if self.epilog:
			formatter.write_paragraph()
			for line in self.epilog.split('\n'):
				formatter.write_text(line)

class windows_noexpand_args: # pragma: no cover
	""" Fixes backward-incompatible issues introduced by click authors in new versions.
	May serve as decorator:
	@windows_noexpand_args
	@click.command(..).
	def ..
	"""
	def __init__(self, cli):
		self._orig = cli
	def __call__(self, *args, **kwargs):
		try:
			if tuple(map(int, click.__version__.split('.'))) >= (8, 0, 1):
				kwargs['windows_expand_args'] = False
		except:
			import traceback
			traceback.print_exc(file=sys.stderr)
		return self._orig(*args, **kwargs)
	def __getattr__(self, name):
		return getattr(self._orig, name)
