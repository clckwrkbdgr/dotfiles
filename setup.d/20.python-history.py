#!/usr/bin/env python
import os, sys
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
import subprocess
from clckwrkbdgr import commands
import clckwrkbdgr.jobsequence.context
trace = context =  clckwrkbdgr.jobsequence.context.init(
		verbose_var='DOTFILES_SETUP_VERBOSE',
		skip_platforms='Windows',
		)

try:
	subprocess.check_output(['python3', '-V'], stderr=subprocess.STDOUT)
except OSError:
	context.done()

def get_site_module_path():
	return Path(subprocess.check_output(['python3', '-c', 'import site; print(site.__file__)']).decode().strip())

UNPATCHED_PYTHON_HISTORY_CODE = """\
            history = os.path.join(os.path.expanduser('~'),
                                   '.python_history')
"""

PATCHED_PYTHON_HISTORY_CODE = """\
            history = os.path.join(os.path.expanduser('~/.state'),
                                   '.python_history')
"""

if UNPATCHED_PYTHON_HISTORY_CODE not in get_site_module_path().read_text():
	context.done()

if not commands.has_sudo_rights():
	trace.info('Have no sudo rights, skipping.')
	context.done()

trace.error('.python_history code is not patched and it will be created each time REPL is executed')
trace.error('Update following file with following code:')
print('--- {0}'.format(get_site_module_path()))
print('+++ {0}'.format(get_site_module_path()))
for line in UNPATCHED_PYTHON_HISTORY_CODE.splitlines():
	print('-' + line)
for line in PATCHED_PYTHON_HISTORY_CODE.splitlines():
	print('+' + line)
sys.exit(1) # TODO way to fix automatically with sudo.
