from __future__ import absolute_import

from unittest import *
from unittest import runner as _runner
def load_tests(loader, tests, pattern): # pragma: no cover -- fixes loading invalid tests, see doctest:
	""" For some reason when its `clckwrkbdgr/unittest/__init__.py`
	instead of `clckwrkbdgr/unittest.py`, unittest discovery finds and loads
	FunctionalTestCase (the original one which is in built-in unittest directory),
	and (of course) fails to execute it, as it is not a properly defined test case.
	So we're here returning empty test list for this module,
	telling unittest discovery to GTFO of here and go being smart elsewhere.
	"""
	import os
	from .test import test_runner
	suite = TestSuite()
	this_dir = os.path.join(os.path.dirname(__file__), 'test')
	unittest_tests = loader.discover(start_dir=this_dir, pattern=pattern)
	suite.addTests(unittest_tests)
	return suite
defaultTestLoader.testMethodPrefix = 'should'

import time
try:
	time.perf_counter
except AttributeError: # pragma: no cover -- py2
	time.perf_counter = time.time

class TimedTextTestResult(_runner.TextTestResult):
	def addSuccess(self, test):
		if self.showAll: # pragma: no cover -- too special conditions, need verbose unit test runner.
			if not hasattr(self, '_test_stopTime') or self._test_stopTime < self._test_startTime:
				self._test_stopTime = time.perf_counter()
			timeTaken = self._test_stopTime - self._test_startTime
			self.stream.write("({0:.3f}s) ".format(timeTaken))
		super(TimedTextTestResult, self).addSuccess(test)
	def startTest(self, test):
		super(TimedTextTestResult, self).startTest(test)
		self._test_startTime = time.perf_counter()
	def stopTest(self, test):
		super(TimedTextTestResult, self).stopTest(test)
		self._test_stopTime = time.perf_counter()

class TimedTextTestRunner(_runner.TextTestRunner):
	resultclass = TimedTextTestResult
_runner.TextTestRunner = TimedTextTestRunner

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
		def setUp(self): # pragma: no cover - may be not called if running tests where no FS test cases requested.
			self.setUpPyfakefs(modules_to_reload=(self.MODULES or []))
	class fs:
		TestCase = ExtendedFSTestCase
except ImportError: # pragma: no cover
	pass

from textwrap import dedent
