#!/usr/bin/env python
import os, sys, subprocess
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		only_platforms='Windows',
		)
import winreg
import clckwrkbdgr.winnt.registry

actual_handler = ''
try:
	actual_handler = clckwrkbdgr.winnt.registry.getvalue(winreg.HKEY_CLASSES_ROOT, r'shebang\Shell\Open\Command', '')
	if actual_handler == r'"C:\WINDOWS\py.exe" "C:\Users\icha\.config\bin\shebang.py" "%L" %*':
		context.done()
except OSError as e:
	context.error(e)
if actual_handler:
	context.die(r"Expected empty value at HKCR\shebang\Shell\Open\Command\@, got: {0}".format(repr(actual_handler)))

command = ['reg', 'import', os.path.expanduser('~/.config/windows/shebang.reg')]
rc = subprocess.call(command)
if 0 != rc:
	context | rc
	context.error("Failed to install shebang registry.")
	context.error("Run under Admin: {0}".format(' '.join(command)))
context.done()
