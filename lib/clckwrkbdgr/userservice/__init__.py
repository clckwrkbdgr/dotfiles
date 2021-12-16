from ._base import *
from . import windows, linux

def by_platform(platform_name): # pragma: no cover -- TODO
	if platform_name == 'Windows':
		return windows.UserService
	if platform_name == 'Linux':
		return linux.UserService
	raise NotImplementedError(platform_name)
