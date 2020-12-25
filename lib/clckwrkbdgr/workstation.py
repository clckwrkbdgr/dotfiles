import sys
import clckwrkbdgr.xdg as xdg
import clckwrkbdgr.utils as utils
import clckwrkbdgr.commands

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
