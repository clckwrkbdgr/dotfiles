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
		script_rootdir=Path.home(),
		skip_platforms='Windows',
		)

try:
	subprocess.check_output(['python3', '-V'], stderr=subprocess.STDOUT)
except OSError:
	context.done()

site_module_path = Path(subprocess.check_output(['python3', '-c', 'import site; print(site.__file__)']).decode().strip())

UNPATCHED_PYTHON_HISTORY_CODE = b"""\
            history = os.path.join(os.path.expanduser('~'),
                                   '.python_history')
"""

PATCHED_PYTHON_HISTORY_CODE = b"""\
            history = os.path.join(os.path.expanduser('~/.state'),
                                   '.python_history')
"""

if UNPATCHED_PYTHON_HISTORY_CODE not in site_module_path.read_bytes():
	context.done()

if not commands.has_sudo_rights():
	trace.info('Have no sudo rights, skipping.')
	context.done()

diff = subprocess.Popen(['diff', '-u', str(site_module_path), '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
patch, _ = diff.communicate(site_module_path.read_bytes().replace(UNPATCHED_PYTHON_HISTORY_CODE, PATCHED_PYTHON_HISTORY_CODE))
diff.wait()

trace.error('.python_history code is not patched and it will be created each time REPL is executed')
trace.error('Update following file with following code:')
trace.error(patch.decode('utf-8', 'replace'))

script = context.script('fix-python3-history.sh', '#!/bin/bash')
script += 'sudo patch -u {0} <<EOF'.format(site_module_path)
script += patch
script += 'EOF'
script += 'rm -f $0'

context.die('or run script {0}'.format(script.filename))
