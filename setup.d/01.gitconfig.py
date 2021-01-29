#!/usr/bin/env python
import os, sys
import configparser
from pathlib import Path
from clckwrkbdgr import xdg

os.chdir(str(xdg.XDG_CONFIG_HOME))

gitconfig = configparser.ConfigParser(strict=False)
gitconfig.read([str(Path('.git')/'config')])
if 'include' in gitconfig and 'path' in gitconfig['include'] and gitconfig['include']['path'] == '../.gitconfig':
	sys.exit()

with (Path('.git')/'config').open('a+') as f:
	f.write('[include]\n')
	f.write('	path=../.gitconfig\n')
