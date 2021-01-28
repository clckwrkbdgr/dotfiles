import os, sys
import subprocess
import configparser
from pathlib import Path
from clckwrkbdgr import xdg

os.chdir(str(xdg.XDG_CONFIG_HOME))

gitconfig = configparser.ConfigParser(strict=False)
gitconfig.read([str(Path('.git')/'config')])
gitmodules = configparser.ConfigParser(strict=False)
gitmodules.read(['.gitmodules'])
if not (set(gitmodules.keys()) - set(gitconfig.keys())):
	sys.exit()

sys.exit(subprocess.call(['git', 'submodule', 'init']))
