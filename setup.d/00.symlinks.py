#!/usr/bin/env python
import os, sys
try:
	from pathlib2 import Path
except ImportError:
	from pathlib import Path
import clckwrkbdgr.fs
from clckwrkbdgr.xdg import XDG_DATA_HOME, XDG_CONFIG_HOME, XDG_CACHE_HOME
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		verbose_var='DOTFILES_SETUP_VERBOSE',
		skip_platforms='Windows',
		)
trace = context # compat

def is_symlink_to(dest, src):
	with clckwrkbdgr.fs.CurrentDir(Path(dest).parent):
		return Path(dest).is_symlink() and Path(src).resolve() == Path(dest).resolve()

def make_symlink(path, real_path):
	real_path = Path(real_path)
	real_path.parent.mkdir(parents=True, exist_ok=True)
	path = Path(path)
	path.parent.mkdir(parents=True, exist_ok=True)
	if path.exists():
		os.rename(str(path), str(path.with_suffix('.bak')))
	os.symlink(str(real_path), str(path))

class XDGSymlinks:
	""" Manages known XDG symlinks in XDG_CONFIG_HOME. """
	def __init__(self):
		self.known = []
	def ensure(self, symlink, real_file):
		""" Creates target 'ensure_xdg_symlink' to ensure that
		symlink exists and points to real_file. If not, symlink is created.
		Also tracks given symlink as known.
		"""
		self.known.append(symlink)
		if not is_symlink_to(symlink, real_file):
			dest, src = symlink, real_file
			make_symlink(dest, src)
	def ignore(self, symlink):
		""" Marks symlink as known without any actions.
		Useful for third-party symlinks.
		"""
		self.known.append(symlink)
	def is_known(self, filename):
		""" Checks if filename is amongst known symlinks. """
		try:
			return any(filename.samefile(known) for known in self.known)
		except:
			return any(filename.absolute() == known.absolute() for known in self.known)

known_symlinks = XDGSymlinks()

if (Path.home()/'.macromedia').exists():
	known_symlinks.ensure(Path.home()/'.macromedia', XDG_DATA_HOME/'macromedia')
if (Path.home()/'.adobe').exists():
	known_symlinks.ensure(Path.home()/'.adobe', XDG_DATA_HOME/'macromedia')
if (XDG_CONFIG_HOME/'w3m').exists():
	known_symlinks.ensure(Path.home()/'.w3m', XDG_CONFIG_HOME/'w3m')
known_symlinks.ensure(Path.home()/'.profile', XDG_CONFIG_HOME/'profile')
known_symlinks.ensure(Path.home()/'.bashrc', XDG_CONFIG_HOME/'bash'/'bashrc')

if (XDG_CONFIG_HOME/'purple').exists():
	known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'certificates', XDG_CACHE_HOME/'purple'/'certificates')
	known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'telegram-purple', XDG_CACHE_HOME/'purple'/'telegram-purple')
	known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'icons', XDG_CACHE_HOME/'purple'/'icons')
	known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'xmpp-caps.xml', XDG_CACHE_HOME/'purple'/'xmpp-caps.xml')
	known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'accels', XDG_CACHE_HOME/'purple'/'accels')
	known_symlinks.ensure(XDG_CONFIG_HOME/'purple'/'logs', XDG_DATA_HOME/'purple'/'logs')

if (XDG_CONFIG_HOME/'freeciv').exists():
	known_symlinks.ensure(Path.home()/'.freeciv', XDG_CONFIG_HOME/'freeciv')
	known_symlinks.ensure(XDG_CONFIG_HOME/'freeciv'/'saves', XDG_DATA_HOME/'freeciv'/'saves')

if (XDG_CONFIG_HOME/'xfce4').exists() and (XDG_CONFIG_HOME/'Terminal').exists():
	known_symlinks.ensure(XDG_CONFIG_HOME/'xfce4'/'terminal', XDG_CONFIG_HOME/'Terminal')

# Third-party symlinks.
known_symlinks.ignore(XDG_CONFIG_HOME/'vim'/'bundle'/'vimoutliner'/'README.detailed')
known_symlinks.ignore(XDG_CONFIG_HOME/'firefox'/'lock')

def find_unknown_symlinks(root, known_symlinks):
	unknown = []
	for root, dirnames, filenames in os.walk(str(root)):
		root = Path(root)
		for filename in filenames + dirnames:
			filename = root/filename
			if not filename.is_symlink():
				continue
			trace.debug(filename)
			if known_symlinks.is_known(filename):
				continue
			unknown.append(filename)
	return unknown

entries = find_unknown_symlinks(XDG_CONFIG_HOME, known_symlinks)
if entries:
	context.die('Found unknown symlinks:\n' + '\n'.join(entries))
