import os, textwrap
import base64
from click.testing import CliRunner
from clckwrkbdgr import unittest
from .. import _base

@_base.config_filter('mock-binary-format')
class MockBase64TextConfig(_base.ConfigFilter):
	""" Mock config format for testing encode/decode part. """
	@classmethod
	def decode(cls, bin_data):
		return base64.b64decode(bin_data).decode('utf-8')
	@classmethod
	def encode(cls, text_repr):
		return base64.b64encode(text_repr.encode('utf-8'))

from .. import cli

class TestCLI(unittest.TestCase):
	def should_decode_incoming_binary_form(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'mock-binary-format', 'enviro'], input=b"SGVsbG8gd29ybGQhCg==\n")
		self.assertEqual(result.output, "Hello world!\n")
	def should_encode_back_to_binary_form(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'mock-binary-format', 'restore'], input="Hello world!\n")
		self.assertEqual(result.output, "SGVsbG8gd29ybGQhCg==")
	def should_smudge_home_dir_in_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'enviro'], input="First: {HOME}\nSecond: {HOME}\n".format(HOME=os.environ['HOME']))
		self.assertEqual(result.output, textwrap.dedent("""\
		First: $HOME
		Second: $HOME
		"""))
	def should_restore_home_dir_in_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'restore'], input='First: $HOME\nSecond: $HOME\n')
		self.assertEqual(result.output, textwrap.dedent("""\
		First: {HOME}
		Second: {HOME}
		""".format(HOME=os.environ['HOME'])))
	def should_fail_on_invalid_custom_env_var(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', '-e' 'invalid_var_def', 'enviro'], input="dummy\n")
		self.assertEqual(result.exit_code, 1)
		self.assertEqual(result.output, '')
	def should_fail_on_unknown_custom_env_var(self):
		runner = CliRunner()
		self.assertIsNone(os.environ.get('INVALID_ENV_VAR'))
		result = runner.invoke(cli.main, ['-f', 'txt', '-e' 'XHOME=$INVALID_ENV_VAR', 'enviro'], input="dummy\n")
		self.assertEqual(result.exit_code, 1)
		self.assertEqual(result.output, '')
	def should_smudge_custom_env_var(self):
		runner = CliRunner()
		os.environ['XHOME'] = os.environ["LOGNAME"]
		result = runner.invoke(cli.main, ['-f', 'txt', '-e' 'XHOME=echo $LOGNAME', 'enviro'], input="First: {XHOME}\nSecond: {XHOME}\n".format(XHOME=os.environ['XHOME']))
		self.assertEqual(result.output, textwrap.dedent("""\
		First: $XHOME
		Second: $XHOME
		"""))
	def should_restore_custom_env_var(self):
		runner = CliRunner()
		os.environ['XHOME'] = os.environ["LOGNAME"]
		result = runner.invoke(cli.main, ['-f', 'txt', '-e', 'XHOME=echo $LOGNAME', 'restore'], input='First: $XHOME\nSecond: $XHOME\n')
		self.assertEqual(result.output, textwrap.dedent("""\
		First: {XHOME}
		Second: {XHOME}
		""".format(XHOME=os.environ['XHOME'])))
	def should_smudge_several_custom_env_vars(self):
		runner = CliRunner()
		os.environ['XHOME'] = "xhome"
		result = runner.invoke(cli.main, ['-f', 'txt', '-e', 'XHOME=$XHOME', '-e', 'USERNAME=$USER', 'enviro'], input="First: {XHOME}\nSecond: {USER}\n".format(XHOME=os.environ['XHOME'], USER=os.environ['USER']))
		self.assertEqual(result.output, textwrap.dedent("""\
		First: $XHOME
		Second: $USERNAME
		"""))
	def should_restore_several_custom_env_vars(self):
		runner = CliRunner()
		os.environ['XHOME'] = os.environ['HOME']
		result = runner.invoke(cli.main, ['-f', 'txt', '-e', 'XHOME=echo $HOME', '-e', 'USERNAME=$USER', 'restore'], input='First: $XHOME\nSecond: $USERNAME\n')
		self.assertEqual(result.output, textwrap.dedent("""\
		First: {XHOME}
		Second: {USER}
		""".format(XHOME=os.environ['XHOME'], USER=os.environ['USER'])))
	def should_sort_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'sort', '_path'], input="b\nc\na\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		a
		b
		c
		"""))
	def should_delete_value_from_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'delete', '_path', 'b'], input="a\nb\nc\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		a
		c
		"""))
	def should_delete_line_with_substring_from_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'delete', '_path', 'eco'], input="first\nsecond\nthird\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		first
		third
		"""))
	def should_delete_regex_from_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'delete', '_path', '^se.on+d$', '--pattern-type', 'regex'], input="first\nsecond\nthird\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		first
		third
		"""))
	def should_replace_substring_in_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'replace', '_path', 'seco', '--with', '2'], input="first\nsecond\nthird\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		first
		2nd
		third
		"""))
	def should_replace_regex_in_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'replace', '_path', '^seco([a-z]+)$', '--pattern-type', 'regex', '--with', '2\\1'], input="first\nsecond\nthird\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		first
		2nd
		third
		"""))
	def should_prettify_plain_text(self):
		runner = CliRunner()
		result = runner.invoke(cli.main, ['-f', 'txt', 'pretty'], input="first\n  second\n\tthird\n")
		self.assertEqual(result.output, textwrap.dedent("""\
		first
		  second
			third
		"""))
	def should_perform_multiple_commands(self):
		self.maxDiff = None
		runner = CliRunner()
		with runner.isolated_filesystem():
			with open('script.sh', 'w') as f:
				f.write(textwrap.dedent("""\
				# Comment
				delete "" --pattern-type regex "^.*remove"
				sort ""
				replace "" --pattern-type regex "seco(nd)" --with "2\\1"
				"""))
			result = runner.invoke(cli.main, ['-f', 'txt', 'script', 'script.sh'], input="second\nthird\nto remove\nfirst\n")
			self.assertEqual(result.output, textwrap.dedent("""\
			first
			2nd
			third
			"""))
	def should_fail_on_unknown_command_in_script(self):
		runner = CliRunner()
		with runner.isolated_filesystem():
			with open('script.sh', 'w') as f:
				f.write(textwrap.dedent("""\
				# Comment
				unknown_command
				sort
				"""))
			result = runner.invoke(cli.main, ['-f', 'txt', 'script', 'script.sh'], input="second\nthird\nto remove\nfirst\n")
			self.assertEqual(result.output, textwrap.dedent("""\
			second
			third
			to remove
			first
			"""))
			self.assertEqual(result.exit_code, 1)
	def should_fail_on_not_a_command_in_script(self):
		runner = CliRunner()
		with runner.isolated_filesystem():
			with open('script.sh', 'w') as f:
				f.write(textwrap.dedent("""\
				# Comment
				get_epilog
				sort
				"""))
			result = runner.invoke(cli.main, ['-f', 'txt', 'script', 'script.sh'], input="second\nthird\nto remove\nfirst\n")
			self.assertEqual(result.output, textwrap.dedent("""\
			second
			third
			to remove
			first
			"""))
			self.assertEqual(result.exit_code, 1)
