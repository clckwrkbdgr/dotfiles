try:
	import sqlite3
except: # pragma: no cover
	sqlite3 = None

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
			return [row for row in cursor]
		finally:
			cursor.close()
	finally:
		conn.close()
	return None
