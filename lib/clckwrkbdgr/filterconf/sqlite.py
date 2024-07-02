import os, tempfile
import re
from . import ConfigFilter, config_filter
from . import convert_pattern
import sqlite3

SharedNamedTemporaryFile = tempfile.NamedTemporaryFile
import platform
if platform.system() == 'Windows': # pragma: no cover
	from ..winnt import fs
	SharedNamedTemporaryFile = fs.SharedNamedTemporaryFile

class ContentWithDB(str):
	def add_db(self, db, _tempfile):
		self._db = db
		self._tempfile = _tempfile
	def replace(self, *args, **kwargs):
		result = str.replace(self, *args, **kwargs)
		result = ContentWithDB(result)
		result.add_db(self._db, self._tempfile)
		return result

@config_filter('sqlite')
class SQLiteConfig(ConfigFilter):
	""" SQLite DB config. """

	@staticmethod
	def get_op(pattern_type):
		if pattern_type == 'regex':
			return 'REGEXP'
		elif pattern_type == 'wildcard':
			return 'LIKE'
		return '=='
	@staticmethod
	def regexp(expr, item):
		return re.match(expr, item) is not None

	@classmethod
	def decode(cls, binary_data):
		""" Converts config from binary form to text representation
		suitable to be stored in VCS.
		By default just treats input as UTF-8 text.
		"""
		_tempfile = SharedNamedTemporaryFile()
		_tempfile.write(binary_data)
		_tempfile.flush()
		os.fsync(_tempfile)
		db = sqlite3.connect(_tempfile.name)
		db.create_function('regexp', 2, cls.regexp)
		content = ContentWithDB('\n'.join(db.iterdump()) + '\n')
		content.add_db(db, _tempfile)
		return content
	@classmethod
	def encode(cls, content_with_db):
		""" Converts text representation back to the original binary form.
		By default just encodes output as UTF-8 text.
		"""
		_tempfile = content_with_db._tempfile
		os.fsync(_tempfile)
		_tempfile.seek(0)
		raw_sql_data = _tempfile.read()
		_tempfile.close()
		return raw_sql_data
	def unpack(self, content):
		if isinstance(content, ContentWithDB):
			self._tempfile = content._tempfile
			self.db = content._db
		else:
			self.db = sqlite3.connect(':memory:')
			self.db.create_function('regexp', 2, self.regexp)
			self.db.cursor().executescript(content)
			self.db.commit()
		return self.db
	def pack(self, data):
		content = '\n'.join(self.db.iterdump()) + '\n'
		if hasattr(self, '_tempfile'):
			content = ContentWithDB(content)
			content.add_db(self.db, self._tempfile)
		self.db.close()
		return content
	def sort(self, path):
		pass # SQLite DB has no option to "sort" its content.
	def delete(self, table, pattern, pattern_type=None):
		if '.' in table:
			table, expression = table.split('.', 1)
			self.db.cursor().execute("DELETE FROM {0} WHERE {1} {2} ?;".format(
				table, expression, self.get_op(pattern_type),
				), (pattern,))
		else:
			self.db.cursor().execute("DELETE FROM {0};".format(
				table,
				))
		self.db.commit()
	def replace(self, table, pattern, substitute, pattern_type=None):
		if '.' in table:
			table, expression = table.split('.', 1)
			self.db.cursor().execute("UPDATE {0} SET {3} WHERE {1} {2} ?;".format(
				table, expression, self.get_op(pattern_type),
				substitute,
				), (pattern,))
		else:
			self.db.cursor().execute("UPDATE {0} SET {1};".format(
				table,
				substitute,
				))
		self.db.commit()
	def pretty(self):
		pass # SQLite DB has no option to "prettify" its content.
