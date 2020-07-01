from __future__ import print_function, unicode_literals
import os, sys, re
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
import clckwrkbdgr.xdg as xdg

userstate_dir = xdg.save_state_path("userstate")

known_userstate_markers = []

def read_config_file(configfile): # pragma: no cover -- TODO reads FS
	"""
	Config file is a plain-test file with markers defined on separate lines.
	Marker should be a correct C identificator:
	- only letters, digits and underscore;
	- cannot start with digit.
	Comments (starting with #) are supported:
	  first_marker
	  # Comment.
	  second_marker # Inlined comment.
	Returns number of successfully read markers.
	"""
	if not configfile.is_file():
		return 0
	id_pattern = re.compile("^[a-zA-Z_][a-zA-Z_0-9]*$")
	valid_markers = 0
	for line in configfile.read_text().splitlines():
		if not line.strip():
			continue
		if line.strip().startswith('#'):
			continue
		value = line.split('#', 1)[0].strip()
		if not id_pattern.match(value):
			print("Marker name does not follow C identificator pattern: {0}".format(value), file=sys.stderr)
			continue
		known_userstate_markers.append(value)
		valid_markers += 1
	return valid_markers

def get_flag(flag): # pragma: no cover -- TODO operates on global state.
	""" Returns True if flag is known and is set, False otherwise. """
	if flag not in known_userstate_markers:
		print("Unknown userstate marker found: '{0}'".format(flag), file=sys.stderr) # TODO use logging.warning instead.
		return False
	flag_file = userstate_dir/flag
	return flag_file.is_file()

def set_flag(flag, value=True): # pragma: no cover -- TODO operates on global state.
	""" Sets flag to specified state (default is True). """
	if flag not in known_userstate_markers:
		print("Unknown userstate marker found: '{0}'".format(flag), file=sys.stderr)
		return False
	flag_file = userstate_dir/flag
	if value and not flag_file.is_file():
		flag_file.touch()
	elif not value and flag_file.is_file():
		os.unlink(str(flag_file))
	return True

def unset_flag(flag): # pragma: no cover -- TODO operates on global state.
	""" Unsets flag. Equivalent of set_flag(flag, False). """
	return set_flag(flag, False)

def list_all_flags(): # pragma: no cover -- TODO operates on global state.
	""" Returns list of all known flags. """
	return known_userstate_markers[:]

def list_current_flags(): # pragma: no cover -- TODO operates on global state.
	""" Yields currently set flags.
	Raises exception when directory is inaccessible.
	"""
	try:
		os.chdir(str(userstate_dir))
	except:
		print("Cannot list directory with current markers: {0}".format(userstate_dir), file=sys.stderr)
		raise
	for entry in userstate_dir.iterdir():
		marker = entry.name
		if marker not in known_userstate_markers:
			print("Unknown userstate marker found: '{0}'".format(marker), file=sys.stderr)
			continue
		yield marker

read_config_file(xdg.XDG_CONFIG_HOME/'userstate.cfg')
read_config_file(Path().home()/'.local'/'userstate.cfg')
