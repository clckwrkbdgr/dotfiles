#!/usr/bin/env python
import os, sys
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.fs
import clckwrkbdgr.jobsequence.context
trace = context = clckwrkbdgr.jobsequence.context.init(
		verbose_var='DOTFILES_SETUP_VERBOSE',
		skip_platforms='Windows',
		)

if not (xdg.XDG_DATA_HOME/'lastfm'/'lastfmsubmitd.conf').exists():
	context.done()

def is_symlink_to(dest, src):
	with clckwrkbdgr.fs.CurrentDir(Path(dest).parent):
		return Path(dest).is_symlink() and Path(src).resolve() == Path(dest).resolve()

if not is_symlink_to('/etc/lastfmsubmitd.conf', xdg.XDG_DATA_HOME/'lastfm'/'lastfmsubmitd.conf'):
	context.die('{0} is not symlink to {1}'.format(
		'/etc/lastfmsubmitd.conf',
		xdg.XDG_DATA_HOME/'lastfm'/'lastfmsubmitd.conf'
		)) # TODO way to fix automatically with sudo.

LASTFMSUBMITD_MONIT = """\
check process lastfmsubmitd with pidfile /var/run/lastfm/lastfmsubmitd.pid
  start program = "/usr/sbin/service lastfmsubmitd restart"
  stop program = "/usr/sbin/service lastfmsubmitd stop"
  group lastfm
"""
MONIT_CONF_DIR = Path('/etc/monit/conf.d/')

def file_has_content(filename, content):
	filename = Path(filename)
	if not filename.is_file():
		return False
	if filename.read_text() != content:
		return False
	return True

if not file_has_content(MONIT_CONF_DIR/'lastfmsubmitd', LASTFMSUBMITD_MONIT):
	trace.error('{0} is missing or does not contain following content:'.format(
		MONIT_CONF_DIR/'lastfmsubmitd',
		))
	print(LASTFMSUBMITD_MONIT)
	sys.exit(1) # TODO way to fix automatically with sudo.

if not os.path.isdir('/run/lastfm'):
	trace.error('Directory {0} is missing.'.format('/run/lastfm'))
	trace.error('Create it and restart lastfmsubmitd service:')
	print('sudo /usr/sbin/service lastfmsubmitd restart')
	sys.exit(1) # TODO way to fix automatically with sudo.
