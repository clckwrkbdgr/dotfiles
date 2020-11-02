import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'

import lz4.block
import clckwrkbdgr.firefox

class TestFirefox(unittest.TestCase):
	def should_compress_mozLz4(self):
		expected = b'mozLz40\0' + lz4.block.compress(b'foobar')
		self.assertEqual(clckwrkbdgr.firefox.compress_mozLz4(b'foobar'), expected)
	def should_decompress_mozLz4(self):
		data = b'mozLz40\0' + lz4.block.compress(b'foobar')
		self.assertEqual(clckwrkbdgr.firefox.decompress_mozLz4(data), b'foobar')
