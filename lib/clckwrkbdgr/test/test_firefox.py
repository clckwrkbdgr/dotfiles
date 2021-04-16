import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'

try:
	import lz4.block
except ImportError: # pragma: no cover
	lz4 = None
import clckwrkbdgr.firefox

class TestFirefox(unittest.TestCase):
	@unittest.skipUnless(lz4, 'lz4.block is not detected.')
	def should_compress_mozLz4(self): # pragma: no cover -- TODO needs mocks instead of just skipping.
		expected = b'mozLz40\0' + lz4.block.compress(b'foobar')
		self.assertEqual(clckwrkbdgr.firefox.compress_mozLz4(b'foobar'), expected)
	@unittest.skipUnless(lz4, 'lz4.block is not detected.')
	def should_decompress_mozLz4(self): # pragma: no cover -- TODO needs mocks instead of just skipping.
		data = b'mozLz40\0' + lz4.block.compress(b'foobar')
		self.assertEqual(clckwrkbdgr.firefox.decompress_mozLz4(data), b'foobar')
