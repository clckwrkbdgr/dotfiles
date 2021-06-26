#!/usr/bin/env python
import sys, subprocess, platform, socket
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
import clckwrkbdgr.xdg as xdg

LOCAL = Path().home()/'.local'
crontabs = [
	xdg.XDG_CONFIG_HOME/'crontab',
	xdg.XDG_CONFIG_HOME/'crontab.{0}'.format(platform.system()),
	xdg.XDG_DATA_HOME/'crontab',
	xdg.XDG_DATA_HOME/'crontab.{0}'.format(platform.system()),
	xdg.XDG_DATA_HOME/'crontab.{0}'.format(socket.gethostname()),
	LOCAL/'crontab',
	LOCAL/'crontab.{0}'.format(platform.system()),
	LOCAL/'crontab.{0}'.format(socket.gethostname()),
	]
crontabs = b''.join(crontab.read_bytes() for crontab in crontabs if crontab.is_file())
p = subprocess.Popen(['crontab'], stdin=subprocess.PIPE, shell=True)
stdout, stderr = p.communicate(crontabs)
assert not stdout and not stderr, (stdout or b'') + (stderr or b'')
sys.exit(p.wait())
