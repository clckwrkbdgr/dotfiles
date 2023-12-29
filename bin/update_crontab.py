#!/usr/bin/env python
import sys, subprocess, platform, socket
import itertools, collections
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
import clckwrkbdgr.xdg as xdg

dirs = [
		xdg.XDG_CONFIG_HOME,
		xdg.XDG_CONFIG_HOME/'local',
		xdg.XDG_DATA_HOME,
		Path().home()/'.local'/'share',
		Path().home()/'.local',
		]
files = [
		'crontab',
		'crontab.{0}'.format(platform.system()),
		'crontab.{0}'.format(socket.gethostname()),
		]
crontabs = list(collections.OrderedDict.fromkeys([dirname/filename for dirname, filename in itertools.product(dirs, files)]))
crontabs = b''.join(crontab.read_bytes() for crontab in crontabs if crontab.is_file())
p = subprocess.Popen(['crontab'], stdin=subprocess.PIPE, shell=True)
stdout, stderr = p.communicate(crontabs)
assert not stdout and not stderr, (stdout or b'') + (stderr or b'')
sys.exit(p.wait())
