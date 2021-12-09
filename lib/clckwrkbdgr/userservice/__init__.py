from ._base import *
from . import windows

def by_platform(platform_name): # pragma: no cover -- TODO
	if platform_name == 'Windows':
		return windows.UserService
	raise NotImplementedError(platform_name)
