import sys, subprocess
from clckwrkbdgr import xdg

current_crontab = subprocess.check_output(['crontab', '-l'])
basic_crontab = (xdg.XDG_CONFIG_HOME/'crontab').read_bytes()
if basic_crontab in current_crontab:
	sys.exit()

sys.exit(subprocess.call(['update_crontab.py']))
