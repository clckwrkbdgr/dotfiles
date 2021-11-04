import os, sys, subprocess
try:
	subprocess.DEVNULL
except AttributeError: # pragma: no cover
	subprocess.DEVNULL = open(os.devnull, 'w')

def is_app_installed(exe_name): # pragma: no cover -- TODO lots of mocks.
	try:
		return 0 == subprocess.call(['which', str(exe_name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	except OSError:
		return False
