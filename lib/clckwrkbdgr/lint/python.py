import os, sys
import ast

def check_syntax(filename, quiet=False):
	try:
		with open(str(filename), 'rb') as f:
			ast.parse(f.read(), filename=str(filename))
		return True
	except:
		if not quiet: # pragma: no cover
			import traceback
			traceback.print_exc()
		return False
