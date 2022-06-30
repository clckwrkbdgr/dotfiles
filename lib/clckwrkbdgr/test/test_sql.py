from clckwrkbdgr import unittest
from clckwrkbdgr import sql

class TestSqlTableRow(unittest.TestCase):
	def should_representt_row_as_string(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(str(row), "{'First':1, 'Second':2, 'Third':'foo'}")
		self.assertEqual(repr(row), "Row((1, 2, 'foo'), ('First', 'Second', 'Third'))")
	def should_compare_rows_as_tuples_of_Values(self):
		row = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		same = sql.Row([1, 2, 'foo'], ['First', 'Second', 'Third'])
		other = sql.Row([1, 3, 'foo'], ['First', 'Second', 'Third'])
		self.assertEqual(row, same)
		self.assertNotEqual(row, other)
		self.assertTrue(row == same)
		self.assertFalse(row != same)
		self.assertFalse(row == other)
		self.assertTrue(row <= same)
		self.assertFalse(row < same)
		self.assertTrue(row <= other)
		self.assertTrue(row < other)
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
		self.assertEqual(row.get_headers(), ('First', 'Second', 'Third'))
		row = sql.Row([1, 2, 'foo'])
		self.assertEqual(row.get_headers(), ('0', '1', '2'))
