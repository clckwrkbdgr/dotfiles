#!/usr/bin/env python
import sys, subprocess, platform, socket
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path

crontabs = [Path(_).expanduser() for _ in [
	'~/.config/crontab', # TODO XDG
	'~/.config/crontab.{0}'.format(platform.system()),
	'~/.local/crontab',
	'~/.local/crontab.{0}'.format(platform.system()),
	'~/.local/crontab.{0}'.format(socket.gethostname()),
	]]
crontabs = b''.join(crontab.read_bytes() for crontab in crontabs if crontab.is_file())
p = subprocess.Popen(['crontab'], stdin=subprocess.PIPE, shell=True)
stdout, stderr = p.communicate(crontabs)
assert not stdout and not stderr
sys.exit(p.wait())
