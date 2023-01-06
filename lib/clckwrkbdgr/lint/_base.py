import os

def check_syntax(filename, quiet=False): # pragma: no cover -- TODO
	ext = os.path.splitext(filename)
	if ext == '.py':
		from . import python
		return python.check_syntax(filename, quiet=quiet)
	elif ext == '.js':
		from . import javascript
		return javascript.check_syntax(filename, quiet=quiet)
	raise NotImplementedError()
