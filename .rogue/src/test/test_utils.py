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
	def should_list_all_subclasses(self):
		class _MyParentClass(object): pass
		class _MyDirectChild(_MyParentClass): pass
		class _MyDirectChildParent(_MyParentClass): pass
		class _MyNonDirectChild(_MyParentClass): pass
		self.assertEqual(sorted(utils.all_subclasses(_MyParentClass), key=lambda cls: cls.__name__), [
			_MyDirectChild,
			_MyDirectChildParent,
			_MyNonDirectChild,
			])
