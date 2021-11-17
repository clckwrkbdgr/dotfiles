import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from clckwrkbdgr import sql

class TestSqlTableRow(unittest.TestCase):
	def should_access_row_by_index(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(row[0], 1)
		self.assertEqual(row[1], 2)
		self.assertEqual(row[2], 'foo')
	def should_access_row_by_name(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(row['First'], 1)
		self.assertEqual(row['Second'], 2)
		self.assertEqual(row['Third'], 'foo')
	def should_access_row_by_attr(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(row.First, 1)
		self.assertEqual(row.Second, 2)
		self.assertEqual(row.Third, 'foo')
	def should_iterate_over_row(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(tuple(row), (1, 2, 'foo'))
	def should_create_sql_row(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(row['First'], 1)
		self.assertEqual(row['Second'], 2)
		self.assertEqual(row['Third'], 'foo')
		self.assertEqual(tuple(row), (1, 2, 'foo'))
	def should_create_sql_row_without_header(self):
		row = sql.Row([1, 2, 'foo'])
		self.assertEqual(row['0'], 1)
		self.assertEqual(row['1'], 2)
		self.assertEqual(row['2'], 'foo')
		self.assertEqual(tuple(row), (1, 2, 'foo'))
	def should_access_headers(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(row.get_headers(), ['First', 'Second', 'Third'])
		row = sql.Row([1, 2, 'foo'])
		self.assertEqual(row.get_headers(), ['0', '1', '2'])
