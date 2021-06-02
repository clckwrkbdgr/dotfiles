#!/usr/bin/env python
import sys, subprocess
import platform
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.fs

def patch_is_applied(destfile, patch):
	with clckwrkbdgr.fs.CurrentDir(Path(destfile).parent):
		return 0 == subprocess.call(['patch', '-R', '-s', '-f', '--dry-run', str(destfile), '-i', str(patch)], stdout=subprocess.DEVNULL)

def apply_patch(destfile, patch):
	return subprocess.call(['patch', str(destfile), '-i', str(patch)])

if platform.system() == 'Windows':
	dest = Path.home()/'.local'/'bin'/'when.pl'
else:
	dest = Path('/usr/bin/when').expanduser()

if not dest.exists():
	context.done()

patch = xdg.XDG_CONFIG_HOME/'patch'/'when-1.1.36-xdg.patch'
if not patch_is_applied(dest, patch):
	context | apply_patch(dest, patch) # TODO needs sudo
	context.done()
