#!/usr/bin/env python
import sys, subprocess, shlex
import platform
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.fs
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		script_rootdir=xdg.XDG_DESKTOP_DIR,
		)

def patch_is_applied(destfile, patch):
	with clckwrkbdgr.fs.CurrentDir(Path(destfile).parent):
		return 0 == subprocess.call(['patch', '-R', '-s', '-f', '--dry-run', str(destfile), '-i', str(patch)], stdout=subprocess.DEVNULL)

def apply_patch(destfile, patch):
	command = ['patch', '--backup', str(destfile), '-i', str(patch)]
	try:
		return subprocess.call(command)
	except Exception as e:
		content.error(str(e))
		script = context.script('patch-when-xdg.sh')
		command = ['sudo'] + command
		script += ' '.join(shlex.quote(x) for x in command)

if platform.system() == 'Windows':
	dest = Path.home()/'.local'/'bin'/'when.pl'
else:
	dest = Path('/usr/bin/when').expanduser()

if not dest.exists():
	context.done()

patch = xdg.XDG_CONFIG_HOME/'patch'/'when-1.1.36-xdg.patch'
if not patch_is_applied(dest, patch):
	context | apply_patch(dest, patch)
	context.done()
