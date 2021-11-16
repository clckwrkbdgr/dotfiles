import os, sys
import clckwrkbdgr.fs

def check_syntax(root): # pragma: no cover -- TODO
	import ast, traceback
	result = True
	for filename in clckwrkbdgr.fs.find(root, exclude_dir_names=['.git', '.svn']):
		if filename.suffix != '.py':
			continue
		try:
			ast.parse(filename.read_bytes(), filename=str(filename))
		except:
			result = False
			traceback.print_exc()
	return result
