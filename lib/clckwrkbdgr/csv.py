from __future__ import absolute_import
import csv

def read_table(filename): # pragma: no cover -- TODO
	""" Expects file with CSV table, where the first row is a header
	and every other row has exactly the same number of cells.
	Returns list of dicts {header_key:cell_value} for each row.
	"""
	result = []
	with open(filename, 'r') as f:
		reader = csv.reader(f)
		header = next(reader)
		for row in reader:
			assert len(row) == len(header), row
			result.append(dict(zip(header, row)))
	return result

