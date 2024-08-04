import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from .. import utils

class TestMetaUtils(unittest.TestCase):
	def should_create_enumeration(self):
		class MyEnum(utils.Enum):
			"""
			first
			Second
			"""
		self.assertEqual(MyEnum.FIRST, 0)
		self.assertEqual(MyEnum.SECOND, 1)
		self.assertEqual(MyEnum.CURRENT, 2)
