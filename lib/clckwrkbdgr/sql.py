try:
	import sqlite3
except: # pragma: no cover
	sqlite3 = None

class Row(object):
	def __init__(self, values, headers=None):
		if headers:
			assert len(values) == len(headers)
		else:
			headers = list(map(str, range(len(values))))
		self._headers = headers
		self._values = values
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
			return [Row(row) for row in cursor]
		finally:
			cursor.close()
	finally:
		conn.close()
	return None
