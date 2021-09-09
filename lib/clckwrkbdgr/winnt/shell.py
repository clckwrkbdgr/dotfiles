import os, platform
import ctypes
try:
	from ctypes import windll, wintypes
except: # pragma: no cover
	from clckwrkbdgr.collections import dotdict
	wintypes = dotdict(DWORD=ctypes.c_int, WORD=ctypes.c_short, BYTE=ctypes.c_byte)
import uuid
try:
	os.PathLike
except AttributeError: # pragma: no cover
	os.PathLike = object

class GUID(ctypes.Structure): # pragma: no cover -- TODO Windows
	_fields_ = [
			("Data1", wintypes.DWORD),
			("Data2", wintypes.WORD),
			("Data3", wintypes.WORD),
			("Data4", wintypes.BYTE * 8)
			] 
	def __init__(self, uuid_):
		ctypes.Structure.__init__(self)
		self.Data1, self.Data2, self.Data3, self.Data4[0], self.Data4[1], rest = uuid_.fields
		for i in range(2, 8):
			self.Data4[i] = rest>>(8 - i - 1)*8 & 0xff

def CoTaskMemFree(*args): # pragma: no cover -- TODO Windows
	_CoTaskMemFree = windll.ole32.CoTaskMemFree     # [4]
	_CoTaskMemFree.restype= None
	_CoTaskMemFree.argtypes = [ctypes.c_void_p]
	return _CoTaskMemFree(*args)

def SHGetKnownFolderPath(*args): # pragma: no cover -- TODO Windows
	_SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath     # [5] [3]
	_SHGetKnownFolderPath.argtypes = [
		ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
	]
	return _SHGetKnownFolderPath(*args)

class SpecialFolder(os.PathLike): # pragma: no cover -- TODO Windows
	""" https://gist.github.com/mkropat/7550097 """
	Desktop = uuid.UUID('{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}')

	def __init__(self, folder_id, path=None):
		self.id = folder_id
		self.path = str(path or self._get(folder_id))
	def _get(self, folder_id):
		user_handle = wintypes.HANDLE(0)
		fid = GUID(folder_id) 
		pPath = ctypes.c_wchar_p()
		S_OK = 0
		path = None
		if S_OK == SHGetKnownFolderPath(ctypes.byref(fid), 0, user_handle, ctypes.byref(pPath)):
			path = pPath.value
		CoTaskMemFree(pPath)
		return path
	def __fspath__(self):
		return self.path
	def __str__(self):
		return self.path
	def __repr__(self):
		return 'SpecialFolder({0}, {1})'.format(repr(self.id), repr(self.path))

if platform.system() == 'Windows': # pragma: no cover -- TODO Windows
	Desktop = SpecialFolder(SpecialFolder.Desktop)
