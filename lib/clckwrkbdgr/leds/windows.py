import platform, shutil
import subprocess, stat
import logging
from collections import namedtuple
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover -- py3 only
	from pathlib import Path

IconResource = namedtuple('IconResource', 'dll_name index')

DESKTOP_INI = """[.ShellClassInfo]
IconResource={dll_name},{icon_index}
[ViewState]
Mode=
Vid=
FolderType=Generic
"""

def _write_desktop_ini(dirpath, icon=None): # pragma: no cover -- TODO
	icon = icon or IconResource(r'C:\WINDOWS\System32\SHELL32.dll', 1)
	dirpath = Path(dirpath)
	if dirpath.exists():
		if platform.system() == 'Windows':
			dirpath.chmod(stat.S_IWRITE)
		subprocess.call(['attrib', '-s', str(dirpath)])
	desktop_ini = (dirpath/'desktop.ini')
	if desktop_ini.exists():
		if platform.system() == 'Windows':
			dirpath.chmod(stat.S_IWRITE)
		subprocess.call(['attrib', '-s', str(desktop_ini)])
	desktop_ini.write_text(DESKTOP_INI.format(icon_index=icon.index, dll_name=icon.dll_name))
	subprocess.call(['attrib', '+s', str(dirpath)])
	subprocess.call(['attrib', '+s', str(desktop_ini)])

def _fix_dos_filename(filename, subst=''): # pragma: no cover -- TODO
	for c in '<>:"/\\|?*':
		filename = filename.replace(c, subst)
	return filename

def _update_icon_cache(): # pragma: no cover
	subprocess.call(["ie4uinit.exe", "-show"])

def _remove_windows_protected_entry(function, path, exc_info): # pragma: no cover
	path = Path(path)
	path.chmod(stat.S_IWRITE)
	try:
		function(path)
	except Exception as e:
		logging.warning("Cannot remove {0}:{1}".format(path, e))

class FolderWidget: # pragma: no cover -- TODO
	def __init__(self, dirpath):
		self.dirpath = Path(dirpath)
	def __enter__(self):
		return self
	def __exit__(self, _1, _2, _3):
		_update_icon_cache()
	def _get_tags(self, entry):
		result = set()
		tagfile = entry/'TAG'
		if tagfile.exists():
			result.add(tagfile.read_text().strip())
		if (entry/'KEEP').exists():
			result.add('KEEP')
		for subentry in entry.iterdir():
			if not subentry.suffix == '.tag':
				continue
			result.add(subentry.stem)
		return result
	def remove(self, title=None, tags=None):
		for entry in self.dirpath.iterdir():
			if entry.name == _fix_dos_filename(title):
				logging.debug("Removing old entry {0} by title...".format(entry, title))
				shutil.rmtree(str(entry), onerror=_remove_windows_protected_entry)
				continue
			entry_tags = self._get_tags(entry)
			if tags and set(tags) & entry_tags:
				logging.debug("Removing old entry {0} with tags {1}...".format(entry, entry_tags))
				shutil.rmtree(str(entry), onerror=_remove_windows_protected_entry)
	def add(self, icon, title, tags=None):
		if tags:
			self.remove(tags=tags)
		filename = _fix_dos_filename(title)
		logging.debug("Creating {0}...".format(filename))
		(self.dirpath/filename).mkdir(exist_ok=True)
		_write_desktop_ini(self.dirpath/filename, icon)
		for tag in tags:
			(self.dirpath/filename/'{0}.tag'.format(tag)).touch()
	def clear(self, keep_tags=None, keep_titles=None):
		kept = []
		for entry in self.dirpath.iterdir():
			if keep_tags:
				entry_tags = self._get_tags(entry)
				if set(keep_tags) & entry_tags:
					logging.debug("Keeping entry as requested: {0}".format(keep_tags))
					kept.append(entry)
					continue
			if keep_titles and str(entry.name) in keep_titles:
				logging.debug("Skipping {0}: present in new content.".format(entry))
				kept.append(entry)
				continue
			shutil.rmtree(str(entry), onerror=_remove_windows_protected_entry)
		return kept
