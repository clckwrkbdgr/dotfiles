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

import re
VERSION = re.compile(r'^When version ([0-9.]+), \(c\).*$')
version_line = subprocess.check_output(['perl', str(dest), '--version']).decode().splitlines()[0]
version = VERSION.match(version_line)
if not version:
	context.warning('Failed to detect version:\n\t' + version_line)
else:
	version = tuple(map(int, version.group(1).split('.')))
	XDG_SUPPORT_VERSION = (1, 1, 45)
	if version >= XDG_SUPPORT_VERSION:
		context.info('Version {0} already supports XDG out of the box.'.format(version))
		context.done()

patch = xdg.XDG_CONFIG_HOME/'patch'/'when-1.1.36-xdg.patch'
if not patch_is_applied(dest, patch):
	context | apply_patch(dest, patch)
	context.done()
