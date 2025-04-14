from clckwrkbdgr import unittest
from .. import entity

class MockEntity(object):
	def __init__(self):
		self.value = 'default'
	def __getstate__(self):
		return {'value': self.value}

class TestStorage(unittest.fs.TestCase):
	MODULES = [entity]
	def should_load_entity_from_storage(self):
		self.fs.create_dir('/data')

		with entity.SerializedEntity.store('/data/entity.json', 'mockentity', MockEntity) as data:
			self.assertEqual(data.value, 'default')

		storage = entity.SerializedEntity('/data/entity.json', 0, entity_name='mockentity')
		mockentity = MockEntity()
		mockentity.value = 'custom'
		storage.reset(mockentity)
		storage.save()

		with entity.SerializedEntity.store('/data/entity.json', 'mockentity', MockEntity) as data:
			self.assertEqual(data.value, 'custom')
