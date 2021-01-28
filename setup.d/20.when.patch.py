import sys, subprocess
from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.fs

def patch_is_applied(destfile, patch):
	with clckwrkbdgr.fs.CurrentDir(Path(destfile).parent):
		return 0 == subprocess.call(['patch', '-R', '-s', '-f', '--dry-run', str(destfile), '-i', str(patch)], stdout=subprocess.DEVNULL)

def apply_patch(destfile, patch):
	return subprocess.call(['patch', str(destfile), '-i', str(patch)])

dest, patch = Path('/usr/bin/when').expanduser(), XDG_CONFIG_HOME/'patch'/'when-1.1.36-xdg.patch'
if not patch_is_applied(dest, patch):
	sys.exit(apply_patch(dest, patch)) # TODO needs sudo
