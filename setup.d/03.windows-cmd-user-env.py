#!/usr/bin/env python
import os, sys, subprocess
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
		only_platforms='Windows',
		)
import winreg
import clckwrkbdgr.winnt.registry

actual_autorun = clckwrkbdgr.winnt.registry.getvalue(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Command Processor', 'AutoRun')
if actual_autorun == r'%USERPROFILE%\.config\bin\user-env.cmd':
	context.done()
if actual_autorun:
	context.die(r"Expected empty value at HKCU\Software\Microsoft\Command Processor\AutoRun, got: {0}".format(repr(actual_autorun)))

def write_reg_value(path, name, value):
	context.warning("Setting {0}\\{1} = {2}".format(path, name, value))
	with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_ALL_ACCESS) as key:
		winreg.SetValueEx(key, name, None, winreg.REG_EXPAND_SZ, value)

write_reg_value(r'Software\Microsoft\Command Processor', 'AutoRun', r'%USERPROFILE%\.config\bin\user-env.cmd')
context.done()
