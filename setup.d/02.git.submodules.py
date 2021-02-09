#!/usr/bin/env python
import os, sys
import subprocess
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
	import re
	class NotStrictConfigParser(configparser.ConfigParser):
		OPTCRE = re.compile( # Overriden to allow whitespaces before options.
				r'\s*(?P<option>[^:=\s][^:=]*)'          # very permissive!
				r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
				# followed by separator
				# (either : or =), followed
				# by any # space/tab
				r'(?P<value>.*)$'                     # everything up to eol
				)
from pathlib import Path
from clckwrkbdgr import xdg

os.chdir(str(xdg.XDG_CONFIG_HOME))

try:
	gitconfig = configparser.ConfigParser(strict=False)
except TypeError: # Py2 does not support not strict INIs.
	gitconfig = NotStrictConfigParser()
gitconfig.read([str(Path('.git')/'config')])
try:
	gitmodules = configparser.ConfigParser(strict=False)
except TypeError: # Py2 does not support not strict INIs.
	gitmodules = NotStrictConfigParser()
gitmodules.read(['.gitmodules'])
if not (set(gitmodules.sections()) - set(gitconfig.sections())):
	sys.exit()

sys.exit(subprocess.call(['git', 'submodule', 'init']))
