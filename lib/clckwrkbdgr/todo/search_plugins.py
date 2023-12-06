import contextlib
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
import clckwrkbdgr.projects

def check_project(rootdir): # pragma: no cover -- TODO
	from io import StringIO
	for module in clckwrkbdgr.projects.qualify(rootdir):
		buf = StringIO() # TODO rewrite project checks to yield search result tuples instead.
		with contextlib.redirect_stdout(buf):
			module.check(rootdir)
		for line in buf.getvalue().splitlines():
			parts = line.split(':', 1)
			if len(parts) == 2:
				yield parts[0], 0, parts[1]
			else:
				yield rootdir, 0, parts[0]
