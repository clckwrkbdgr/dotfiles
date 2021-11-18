try:
	import sqlite3
except: # pragma: no cover
	sqlite3 = None
import functools

@functools.total_ordering
class Row(object):
	def __init__(self, values, headers=None):
		if headers:
			assert len(values) == len(headers)
		else:
			headers = map(str, range(len(values)))
		self._headers = tuple(headers)
		self._values = tuple(values)
	def __str__(self):
		return '{' + ', '.join('{0}:{1}'.format(repr(header), repr(value)) for header, value in zip(self._headers, self._values)) + '}'
	def __repr__(self):
		return '{0}({1}, {2})'.format(self.__class__.__name__, repr(self._values), repr(self._headers))
	def __eq__(self, other):
		return self._values == tuple(other)
	def __ne__(self, other):
		return self._values != tuple(other)
	def __lt__(self, other):
		return self._values < tuple(other)
	def get_headers(self):
		return self._headers
	def __iter__(self):
		return iter(self._values)
	def __getitem__(self, name):
		try:
			return self._values[name]
		except:
			index = self._headers.index(name)
			return self._values[index]
	def __getattr__(self, name):
		index = self._headers.index(name)
		return self._values[index]

def execute(database, query): # pragma: no cover -- TODO
	conn = sqlite3.connect(database)
	conn.text_factory = str # To prevent some dummy encoding bug.
	try:
		try:
			cursor = conn.cursor()
			cursor.execute(query)
			conn.commit()
		finally:
			cursor.close()
	finally:
		conn.close()

def select(database, query): # pragma: no cover -- TODO
	conn = sqlite3.connect(database)
	conn.text_factory = str # To prevent some dummy encoding bug.
	try:
		try:
			cursor = conn.cursor()
			cursor.execute(query)
			conn.commit()
			headers = tuple(_[0] for _ in cursor.description)
			return [Row(row, headers) for row in cursor]
		finally:
			cursor.close()
	finally:
		conn.close()
	return None
