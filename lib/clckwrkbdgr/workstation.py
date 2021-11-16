import sys
import clckwrkbdgr.xdg as xdg
import clckwrkbdgr.utils as utils
import clckwrkbdgr.commands
import logging

def _run_event_script(event_name):
	script_dir = xdg.save_data_path('workstation')
	script = script_dir/('{0}.py'.format(event_name))
	if not script.is_file():
		return True
	rc = clckwrkbdgr.commands.run_command_and_collect_output([sys.executable, str(script)])
	return rc == 0

def onlogin():
	""" Performs actions on login to workstation.

	Tries to execute $XDG_DATA_HOME/workstation/onlogin.py using current executable.
	"""
	return _run_event_script('onlogin')

def onlogout():
	""" Performs actions on logout from workstation.

	Tries to execute $XDG_DATA_HOME/workstation/onlogout.py using current executable.
	"""
	return _run_event_script('onlogout')

def onlock():
	""" Performs actions when workstation is locked.

	Tries to execute $XDG_DATA_HOME/workstation/onlock.py using current executable.
	"""
	return _run_event_script('onlock')

def onunlock():
	""" Performs actions when workstation is unlocked.

	Tries to execute $XDG_DATA_HOME/workstation/onunlock.py using current executable.
	"""
	return _run_event_script('onunlock')

def _is_windows_workstation_locked(threshold=0.5): # pragma: no cover
	""" From https://stackoverflow.com/questions/34514644/in-python-3-how-can-i-tell-if-windows-is-locked
	There is no dedicated API to check if workstation is locked or not.
	See comments below for various workarounds.
	"""
	import ctypes, time, subprocess
	user32 = ctypes.windll.user32

	result = 0
	total = 0

	# Locked workstation might have no foreground window at all.
	total += 1
	hwnd = user32.GetForegroundWindow()
	logging.debug('IsWorkstationLocked: foreground hwnd = {0}'.format(hwnd))
	if hwnd == 0:
		result += 1
	else:
		# If it does, we'll check its caption - it should be 'Windows Default Lock Screen'
		total += 1
		title = ctypes.create_string_buffer(255)
		rc = user32.GetWindowTextA(hwnd, title, 255)
		value = title.value
		logging.debug('IsWorkstationLocked: title = {0}'.format(repr(value)))
		if not value or b'Lock Screen' in value:
			result += 1

	# If not, we'll check if Lock screen application is present in the task list.
	total += 1
	tasklist = [line
			for line
			in subprocess.check_output('TASKLIST').decode('utf-8', 'replace').splitlines()
			if 'LogonUI.exe' in line
			]
	logging.debug('IsWorkstationLocked: logonui processes = {0}'.format(repr(tasklist)))
	if tasklist:
		result += 1

	prob_locked = float(result) / float(total)
	logging.debug('IsWorkstationLocked: determined as locked with probability {0}'.format(prob_locked))
	if prob_locked <= threshold:
		logging.debug('IsWorkstationLocked: probability does not exceed threshold {0}, resetting to 0'.format(threshold))
		prob_locked = 0
	return prob_locked

def is_locked(): # pragma: no cover -- TODO
	""" Returns True if workstation is locked.
	Due to some issues on Windows can return float number [0; 1) depending on how sure winapi is that workstation is actually locked.
	"""
	if platform.system() == 'Windows':
		return _is_windows_workstation_locked(threshold=0.5)
	return False # FIXME !!! For Unix/Linux.

import click

@click.group()
def cli(): # pragma: no cover
	pass

@cli.command('onunlock')
@utils.exits_with_return_value
def command_onunlock(): # pragma: no cover
	""" Performs commands intended to be run on workstation unlock event. """
	return onunlock()

@cli.command('onlock')
@utils.exits_with_return_value
def command_onlock(): # pragma: no cover
	""" Performs commands intended to be run on workstation lock event. """
	return onlock()

@cli.command('onlogin')
@utils.exits_with_return_value
def command_onlogin(): # pragma: no cover
	""" Performs commands intended to be run on workstation login. """
	return onlogin()

@cli.command('onlogout')
@utils.exits_with_return_value
def command_onlogout(): # pragma: no cover
	""" Performs commands intended to be run on workstation logout. """
	return onlogout()

if __name__ == '__main__': # pragma: no cover
	cli()
