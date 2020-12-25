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
