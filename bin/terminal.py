import sys, subprocess

args = sys.argv[1:]
if not args:
	print('Usage: terminal [<command> [<args...>]]')
	sys.exit(1)

rc = subprocess.call(['wt'] + args, shell=True)
if rc != 0: # No terminal available, using conhost.
	rc = subprocess.call(['start', 'cmd', '/k'] + args, shell=True)

sys.exit(rc)
