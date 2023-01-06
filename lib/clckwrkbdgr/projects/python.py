import os, sys
import clckwrkbdgr.fs
from .. import lint

def check_syntax(root): # pragma: no cover -- TODO
	import ast, traceback
	result = True
	for filename in clckwrkbdgr.fs.find(root, exclude_dir_names=['.git', '.svn']):
		if filename.suffix != '.py':
			continue
		if not lint.check_syntax(filename):
			result = False
	return result
