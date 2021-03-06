#!/usr/bin/env python
import os, sys
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
from clckwrkbdgr import xdg
from clckwrkbdgr import commands
import clckwrkbdgr.jobsequence.context
trace = context = clckwrkbdgr.jobsequence.context.init(
		verbose_var='DOTFILES_SETUP_VERBOSE',
		skip_platforms='Windows',
		)

if not commands.has_sudo_rights():
	trace.info('Have not sudo rights, skipping.')
	context.done()

etc_config_file = Path('/etc/X11/app-defaults/XXkb')
if not etc_config_file.exists():
	context.die('{0} is not found, cannot add XXkb settings.'.format(etc_config_file)) # TODO can we create this file if it is absent?

Xresources = xdg.XDG_CONFIG_HOME/'Xresources'
local_XXkb = set([line for line in Xresources.read_text().splitlines() if line.startswith('XXkb.')])
missing = local_XXkb - set(etc_config_file.read_text().splitlines())
if not missing:
	context.done()

trace.error('These XXkb config lines are not present in {0}:'.format(etc_config_file))
for line in missing:
	print(line)
sys.exit(1) # TODO way to fix automatically with sudo.
