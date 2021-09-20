from ctypes import Structure, c_uint, sizeof, byref
try:
	from ctypes import windll
except: # pragma: no cover
	pass

class LASTINPUTINFO(Structure):
	_fields_ = [
			('cbSize', c_uint),
			('dwTime', c_uint),
			]

def get_idle_msec(): # pragma: no cover -- TODO WinApi call
	""" Returns idle time (time since last user input - mouse, keyboard) in milliseconds. """
	lastInputInfo = LASTINPUTINFO()
	lastInputInfo.cbSize = sizeof(lastInputInfo)
	windll.user32.GetLastInputInfo(byref(lastInputInfo))
	millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
	return millis

def IsRemoteSession(): # pragma: no cover -- TODO WinApi call
	# You should not use GetSystemMetrics(SM_REMOTESESSION) to determine if your application is running in a remote session in Windows 8 and later or Windows Server 2012 and later if the remote session may also be using the RemoteFX vGPU improvements to the Microsoft Remote Display Protocol (RDP). In this case, GetSystemMetrics(SM_REMOTESESSION) will identify the remote session as a local session.
	# Your application can check the following registry key to determine whether the session is a remote session that uses RemoteFX vGPU. If a local session exists, this registry key provides the ID of the local session.
	#    HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Terminal Server\GlassSessionId
	user32 = ctypes.windll.user32
	SM_REMOTESESSION = 0x1000
	return user32.GetSystemMetrics(SM_REMOTESESSION)

def SwapMouseButton(do_swap): # pragma: no cover -- TODO WinApi call
	user32 = ctypes.windll.user32
	return user32.SwapMouseButton(1 if do_swap else 0)
