import click

""" Custom extensions for click CLI API. """

class RawEpilogGroup(click.Group): # pragma: no cover
	def format_epilog(self, ctx, formatter):
		if self.epilog:
			formatter.write_paragraph()
			for line in self.epilog.split('\n'):
				formatter.write_text(line)
