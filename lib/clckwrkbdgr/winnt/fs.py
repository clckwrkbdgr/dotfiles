import os
import tempfile

NULL                        = 0
CREATE_NEW                  = 1
CREATE_ALWAYS               = 2
OPEN_EXISTING               = 3
OPEN_ALWAYS                 = 4
TRUNCATE_EXISTING           = 5
FILE_SHARE_READ             = 0x00000001
FILE_SHARE_WRITE            = 0x00000002
FILE_SHARE_DELETE           = 0x00000004
FILE_SHARE_VALID_FLAGS      = 0x00000007
FILE_ATTRIBUTE_NORMAL       = 0x00000080
GENERIC_WRITE               = 0x40000000
GENERIC_READ                = 0x80000000
_ACCESS_MASK = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
_ACCESS_MAP  = {os.O_RDONLY : GENERIC_READ,
					 os.O_WRONLY : GENERIC_WRITE,
					 os.O_RDWR   : GENERIC_READ | GENERIC_WRITE}
_CREATE_MASK = os.O_CREAT | os.O_EXCL | os.O_TRUNC
_CREATE_MAP  = {0                                   : OPEN_EXISTING,
				 os.O_EXCL                           : OPEN_EXISTING,
				 os.O_CREAT                          : OPEN_ALWAYS,
				 os.O_CREAT | os.O_EXCL              : CREATE_NEW,
				 os.O_CREAT | os.O_TRUNC | os.O_EXCL : CREATE_NEW,
				 os.O_TRUNC                          : TRUNCATE_EXISTING,
				 os.O_TRUNC | os.O_EXCL              : TRUNCATE_EXISTING,
				 os.O_CREAT | os.O_TRUNC             : CREATE_ALWAYS}

class SharedNamedTemporaryFile: # pragma: no cover -- TODO Windows only
	def __init__(self):
		self.f = tempfile.NamedTemporaryFile(delete=False)
		self.f.close()
		self.name = self.f.name

		import msvcrt
		import _winapi
		share_flags = FILE_SHARE_VALID_FLAGS
		flags = os.O_RDWR
		access_flags = _ACCESS_MAP[flags & _ACCESS_MASK]
		create_flags = _CREATE_MAP[flags & _CREATE_MASK]
		attrib_flags = FILE_ATTRIBUTE_NORMAL
		handle = _winapi.CreateFile(self.name, access_flags, share_flags, NULL,
							  create_flags, attrib_flags, NULL)
		fd = msvcrt.open_osfhandle(handle, flags | os.O_NOINHERIT)
		self.f = os.fdopen(fd, 'r+b')
	def __enter__(self):
		return self
	def __exit__(self, *_args):
		self.close()
		assert not os.path.exists(self.name), self.name

	def fileno(self):
		return self.f.fileno()
	def flush(self):
		return self.f.flush()
	def seek(self, *args):
		return self.f.seek(*args)
	def read(self):
		return self.f.read()
	def write(self, *args):
		return self.f.write(*args)
	def close(self):
		result = self.f.close()
		if os.path.exists(self.name):
			try:
				os.unlink(self.name)
			except:
				pass
		return result
