#!/usr/bin/env python
r""" Utility to detect and execute files with shebang lines.

Can be used on Windows to run executable files without extensions:
0. Have Python installed and associated with *.py files.
1. Ensure that this script is present in `%USERPROFILE%\.config\bin`
2. Run following `cmd` lines (as Administrator):
	ftype shebang=%USERPROFILE%\.config\bin\shebang.py "%1" %*
	assoc .=shebang
	setx /m PATHEXT "%PATHEXT%;."
3. Reboot.

For Windows it can run as Windows paths (C:\...), so Unix-like strings.
For latter, it knows some predefined interpreters (python/python2/python3),
and also can detect /usr/bin/env and use its argument as command.
"""
from __future__ import print_function
import os, sys, subprocess, shlex
import logging


args = sys.argv[1:]
if args and args[0] == '--debug':
	logging.getLogger().setLevel(logging.DEBUG)
	args = args[1:]
if not args:
	logging.error('shebang: no command is specified, nothing to do.')
	sys.exit(1)
command, args = args[0], args[1:]
logging.debug('command: {0} {1}'.format(repr(command), args))
try:
	with open(command, 'rb') as f:
		headline = f.readline()
		logging.debug('headline: {0}'.format(repr(headline)))
except Exception as e:
	logging.error('shebang: failed to read shebang from file: {0}'.format(command))
	sys.exit(1)
if not headline.startswith(b'#!'):
	logging.error('shebang: file "{0}" does not start with shebang'.format(command))
	sys.exit(1)
interpreter = headline[2:].strip()
logging.debug('interpreter: {0}'.format(repr(interpreter)))
if not os.path.exists(interpreter):
	import platform
	if platform.system() == 'Windows':
		logging.debug('Detected Windows. Trying to convert shebang interpreter...')
		if interpreter.startswith(b'/usr/bin/env '):
			interpreter = interpreter.split(None, 1)[1]
			logging.debug('/usr/bin/env: running as {0}'.format(repr(interpreter)))
		else:
			builtin_interpreters = {
					b'/usr/bin/python' : b'python',
					b'/usr/bin/python2' : b'py -2',
					b'/usr/bin/python3' : b'py -3',
					}
			if interpreter in builtin_interpreters:
				interpreter = builtin_interpreters[interpreter]
				logging.debug('known interpreter: running as {0}'.format(repr(interpreter)))
interpreter = shlex.split(interpreter.decode(errors='replace'))
command_line = interpreter + [command] + args
logging.debug('full command line: {0}'.format(command_line))
try:
	rc = subprocess.call(command_line)
except Exception as e:
	logging.error('shebang: failed to execute command {1}: {0}'.format(e, command_line))
	sys.exit(1)
logging.debug('rc: {0}'.format(rc))
sys.exit(rc)
