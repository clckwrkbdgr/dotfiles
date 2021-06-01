import os
import ctypes
from ctypes import windll, wintypes
import uuid
try:
	os.PathLike
except AttributeError:
	os.PathLike = object

class GUID(ctypes.Structure):
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

_CoTaskMemFree = windll.ole32.CoTaskMemFree     # [4]
_CoTaskMemFree.restype= None
_CoTaskMemFree.argtypes = [ctypes.c_void_p]

_SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath     # [5] [3]
_SHGetKnownFolderPath.argtypes = [
		ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)
] 

class SpecialFolder(os.PathLike):
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
		if S_OK == _SHGetKnownFolderPath(ctypes.byref(fid), 0, user_handle, ctypes.byref(pPath)):
			path = pPath.value
		_CoTaskMemFree(pPath)
		return path
	def __fspath__(self):
		return self.path
	def __str__(self):
		return self.path
	def __repr__(self):
		return 'SpecialFolder({0}, {1})'.format(repr(self.id), repr(self.path))

Desktop = SpecialFolder(SpecialFolder.Desktop)
