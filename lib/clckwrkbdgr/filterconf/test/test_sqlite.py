import os, tempfile
import textwrap
import sqlite3
from clckwrkbdgr import unittest
from clckwrkbdgr.filterconf.sqlite import SQLiteConfig, ContentWithDB

DB_SCHEME = """BEGIN TRANSACTION;
CREATE TABLE table_name (name string, value int);
INSERT INTO "table_name" VALUES('foo',1);
INSERT INTO "table_name" VALUES('bar',2);
COMMIT;
"""

class TestSQLiteBinaryContent(unittest.TestCase):
	def should_keep_custom_attrs_with_replacing_values_in_content_with_db(self):
		content = ContentWithDB(DB_SCHEME)
		content.add_db('foo', 'bar')
		content = content.replace('INSERT', 'OUTSERT')
		self.assertEqual(content._db, 'foo')
		self.assertEqual(content._tempfile, 'bar')
	def should_parse_binary_stream_as_sqlite_db_file(self):
		with tempfile.NamedTemporaryFile() as f:
			db = sqlite3.connect(f.name)
			db.cursor().executescript(DB_SCHEME)
			db.commit()
			db.close()
			os.fsync(f)
			f.seek(0)
			raw_sql_data = f.read()
		try:
			content = SQLiteConfig.decode(raw_sql_data)
			self.assertEqual(content, DB_SCHEME)
			self.assertTrue(hasattr(content, '_db'))
			self.assertTrue(hasattr(content, '_tempfile'))
		finally:
			content._tempfile.close()
	def should_encode_sqlite_db_back(self):
		with tempfile.NamedTemporaryFile() as f:
			db = sqlite3.connect(f.name)
			db.cursor().executescript(DB_SCHEME)
			db.commit()
			db.close()
			os.fsync(f)
			f.seek(0)
			raw_sql_data = f.read()
		content = SQLiteConfig.decode(raw_sql_data)
		raw_sql_data = SQLiteConfig.encode(content)
		with tempfile.NamedTemporaryFile() as f:
			f.write(raw_sql_data)
			db = sqlite3.connect(f.name)
			content = '\n'.join(db.iterdump()) + '\n'
			db.close()
		self.assertEqual(content, DB_SCHEME)
	def should_reuse_db_connection_from_encode_stage(self):
		with tempfile.NamedTemporaryFile() as f:
			db = sqlite3.connect(f.name)
			db.cursor().executescript(DB_SCHEME)
			db.commit()
			db.close()
			os.fsync(f)
			f.seek(0)
			raw_sql_data = f.read()
		content = SQLiteConfig.decode(raw_sql_data)
		with SQLiteConfig(content) as filter:
			filter.replace("table_name.name", "bar", "name='baz'")
		raw_sql_data = SQLiteConfig.encode(filter.content)
		with tempfile.NamedTemporaryFile() as f:
			f.write(raw_sql_data)
			db = sqlite3.connect(f.name)
			content = '\n'.join(db.iterdump()) + '\n'
			db.close()
		self.assertEqual(content, DB_SCHEME.replace('bar', 'baz'))

class TestSQLiteConfig(unittest.TestCase):
	def should_sort_and_prettify(self):
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.sort('')
		self.assertEqual(filter.content, DB_SCHEME)

		with SQLiteConfig(DB_SCHEME) as filter:
			filter.pretty()
		self.assertEqual(filter.content, DB_SCHEME)
	def should_delete_rows_unconditionally(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.delete("table_name", "")
		self.assertEqual(filter.content, expected)
	def should_delete_row_with_exact_value(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('foo',1);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.delete("table_name.name", "bar")
		self.assertEqual(filter.content, expected)
	def should_delete_row_by_wildcard(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('foo',1);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.delete("table_name.name", "b%", pattern_type='wildcard')
		self.assertEqual(filter.content, expected)
	def should_delete_row_by_regexp(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('bar',2);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.delete("table_name.(name || value)", "f.*[0-9]$", pattern_type='regex')
		self.assertEqual(filter.content, expected)
	def should_replace_in_rows_unconditionally(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('foo',666);
		INSERT INTO "table_name" VALUES('bar',666);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.replace("table_name", "bar", "value=666")
		self.assertEqual(filter.content, expected)
	def should_replace_in_row_with_exact_value(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('foo',1);
		INSERT INTO "table_name" VALUES('bar',666);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.replace("table_name.name", "bar", "value=666")
		self.assertEqual(filter.content, expected)
	def should_replace_in_row_by_wildcard(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('foo',1);
		INSERT INTO "table_name" VALUES('bar',666);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.replace("table_name.name", "b%", "value=666", pattern_type='wildcard')
		self.assertEqual(filter.content, expected)
	def should_replace_in_row_by_regexp(self):
		expected = textwrap.dedent("""\
		BEGIN TRANSACTION;
		CREATE TABLE table_name (name string, value int);
		INSERT INTO "table_name" VALUES('foo',666);
		INSERT INTO "table_name" VALUES('bar',2);
		COMMIT;
		""")
		with SQLiteConfig(DB_SCHEME) as filter:
			filter.replace("table_name.(name || value)", "f.*[0-9]$", "value=666", pattern_type='regex')
		self.assertEqual(filter.content, expected)
