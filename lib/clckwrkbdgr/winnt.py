from ctypes import Structure, windll, c_uint, sizeof, byref

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
