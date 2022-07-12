from __future__ import absolute_import

from unittest import *
defaultTestLoader.testMethodPrefix = 'should'

try:
	TestCase.assertCountEqual
except AttributeError: # pragma: no cover -- py2 only
	from collections import Counter
	TestCase.assertCountEqual = lambda self, actual, expected: self.assertEqual(
			Counter([(frozenset(item) if isinstance(item, set) else item) for item in actual]),
			Counter([(frozenset(item) if isinstance(item, set) else item) for item in expected]),
			)

try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'

try:
	from pyfakefs import fake_filesystem_unittest
	class ExtendedFSTestCase(fake_filesystem_unittest.TestCase):
		MODULES = None # Modules to reload.
		def setUp(self):
			self.setUpPyfakefs(modules_to_reload=(self.MODULES or []))
	class fs:
		TestCase = ExtendedFSTestCase
except ImportError: # pragma: no cover
	pass

from textwrap import dedent
