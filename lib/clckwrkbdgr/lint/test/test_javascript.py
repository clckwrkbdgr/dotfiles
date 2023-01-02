from ... import unittest
from .. import javascript

class TestJSSyntax(unittest.TestCase):
	@unittest.mock.patch('subprocess.call', side_effect=[0, 1])
	def should_check_JS_syntax(self, subprocess_call):
		self.assertTrue(javascript.check_syntax('good.js'))
		self.assertFalse(javascript.check_syntax('bad.js'))
		subprocess_call.assert_has_calls([
			unittest.mock.call(['node', '--check', 'good.js']),
			unittest.mock.call(['node', '--check', 'bad.js']),
			])
