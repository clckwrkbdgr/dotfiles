from __future__ import absolute_import
import os, platform
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
from collections import defaultdict
from clckwrkbdgr import xdg

def get_swap_dir(): # pragma: no cover -- TODO os, FS
	""" Returns root dir for swap files. """
	if platform.system() == 'Windows':
		tempdir = Path(os.environ['TEMP'])
	return Path('/var/tmp')

def currently_opened_files(): # pragma: no cover -- TODO os, FS
	""" Yields pairs (pid, filename) for currently opened files. """
	swapdir = get_swap_dir()
	for entry in swapdir.iterdir():
		if entry.suffix != '.swp':
			continue
		try:
			data = entry.read_bytes()
		except:
			continue
		if not data.startswith(b'b0VIM'):
			continue
		pid = int.from_bytes(data[24:24+4], byteorder='little')
		filename = Path(data[108:108+256].rstrip(b'\x00').decode()).expanduser().absolute()
		yield pid, filename

def list_vimsise(): # pragma: no cover -- TODO os, FS
	""" Returns current vimsize entries (Windows and GVIM only).
	Result is a dict {size: [list of instances that have this size]}
	"""
	size_file = xdg.XDG_STATE_HOME/'_vimsize'
	sizes = defaultdict(list)
	for entry in size_file.read_text().splitlines():
		name, size = entry.split(None, 1)
		sizes[size].append(name)
	return sizes
