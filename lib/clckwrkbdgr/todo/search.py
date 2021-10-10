try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path

def search_in_line(line, pattern):
	""" Splits string line by patterns.
	Pattern MUST be compiled regexp and MUST contain enclosing parenthesis.
	Returns list of strings, always odd number of element and pattern matches are at odd positions.
	If there were no occurences, returns None.
	"""
	matches = pattern.split(line)
	if len(matches) <= 1:
		return None
	return matches

def search_in_bytes(byte_content, pattern, encoding='utf-8'):
	""" Searches for matching lines in content.
	Pattern MUST be compiled regexp and MUST contain enclosing parenthesis.
	Yields pairs (<line_number>, [<matches>])
	Line numbers start with 1.
	See search_in_line() for the format of <matches> sequence.
	If any exception is encountered, yields pair (0, <exception object).
	"""
	for index, line in enumerate(byte_content.splitlines(), 1):
		try:
			line = line.decode(encoding, 'replace')
			matches = search_in_line(line, pattern)
			if matches:
				yield index, matches
		except Exception as e: # pragma: no cover
			yield 0, e

def search_in_file(filename, pattern, encoding='utf-8'):
	""" Searches for matching lines in given file (if exists).
	Pattern MUST be compiled regexp and MUST contain enclosing parenthesis.
	Yields pairs (<line_number>, [<matches>])
	Line numbers start with 1.
	See search_in_line() for the format of <matches> sequence.
	If any exception is encountered, yields pair (0, <exception object).
	"""
	filename = Path(filename)
	try:
		if not filename.exists():
			return
		for line_number, search_result in search_in_bytes(filename.read_bytes(), pattern):
			yield line_number, search_result
	except Exception as e: # pragma: no cover
		yield 0, e
