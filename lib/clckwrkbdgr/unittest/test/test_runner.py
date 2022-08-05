from .. import runner
from .. import python
from .. import shell
from .. import javascript

import unittest

class TestDummy(unittest.TestCase):
	def should_ensure_that_tests_are_loaded_from_custom_unittest_submodule(self):
		self.assertTrue(True)
