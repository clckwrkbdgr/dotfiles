import sys
import logging
trace = logging.getLogger('setup')
from pathlib import Path
from clckwrkbdgr import xdg

etc_config_file = '/etc/X11/app-defaults/XXkb'

Xresources = xdg.XDG_CONFIG_HOME/'Xresources'
local_XXkb = set([line for line in Xresources.read_text().splitlines() if line.startswith('XXkb.')])
missing = local_XXkb - set(Path(etc_config_file).read_text().splitlines())
if not missing:
	sys.exit()

trace.error('These XXkb config lines are not present in {0}:'.format(etc_config_file))
for line in missing:
	print(line)
sys.exit(1) # TODO way to fix automatically with sudo.
