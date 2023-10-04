from ... import unittest
from ... import fs
from .. import util

class MockEntity(object):
	def __init__(self):
		self.value = 'default'
	def __getstate__(self):
		return {'value': self.value}

class TestStorage(unittest.fs.TestCase):
	MODULES = [util]
	def should_load_entity_from_storage(self):
		self.fs.create_dir('/data')

		with util.stored_entity('/data/entity.json', 'mockentity', MockEntity) as entity:
			self.assertEqual(entity.value, 'default')

		storage = fs.SerializedEntity('/data/entity.json', 0, entity_name='mockentity')
		mockentity = MockEntity()
		mockentity.value = 'custom'
		storage.reset(mockentity)
		storage.save()

		with util.stored_entity('/data/entity.json', 'mockentity', MockEntity) as entity:
			self.assertEqual(entity.value, 'custom')
