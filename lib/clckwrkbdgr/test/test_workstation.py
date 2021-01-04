import unittest
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
unittest.defaultTestLoader.testMethodPrefix = 'should'
import os, sys
import clckwrkbdgr.workstation as workstation
try: # pragma: no cover
	import pathlib2 as pathlib
	pathlib_module = 'pathlib2'
	from pathlib2 import Path
except ImportError: # pragma: no cover
	import pathlib
	pathlib_module = 'pathlib'
	from pathlib import Path

class TestWorkstationEvents(unittest.TestCase):
	@mock.patch('clckwrkbdgr.xdg.save_data_path')
	@mock.patch('clckwrkbdgr.commands.run_command_and_collect_output')
	@mock.patch(pathlib_module + '.Path.is_file')
	def should_run_arbitrary_event_script(self, is_file, run_command, save_data_path):
		mock_root_path = Path('/path/to/share/workstation')
		save_data_path.return_value = mock_root_path
		run_command.return_value = 0
		is_file.return_value = True

		result = workstation._run_event_script('myevent')
		self.assertTrue(result)
		save_data_path.assert_called_once_with('workstation')
		run_command.assert_called_once_with([sys.executable, str(mock_root_path/'myevent.py')])
	@mock.patch('clckwrkbdgr.xdg.save_data_path')
	@mock.patch('clckwrkbdgr.commands.run_command_and_collect_output')
	@mock.patch(pathlib_module + '.Path.is_file')
	def should_not_run_event_script_if_does_not_exist(self, is_file, run_command, save_data_path):
		save_data_path.return_value = Path('/path/to/share/workstation')
		run_command.return_value = 0
		is_file.return_value = False

		result = workstation._run_event_script('myevent')
		self.assertTrue(result)
		save_data_path.assert_called_once_with('workstation')
		run_command.assert_not_called()
	@mock.patch('clckwrkbdgr.xdg.save_data_path')
	@mock.patch('clckwrkbdgr.commands.run_command_and_collect_output')
	@mock.patch(pathlib_module + '.Path.is_file')
	def should_recognize_default_events(self, is_file, run_command, save_data_path):
		mock_root_path = Path('/path/to/share/workstation')
		save_data_path.return_value = mock_root_path
		run_command.return_value = 0
		is_file.return_value = True

		run_command.reset_mock()
		self.assertTrue(workstation.onlogin())
		run_command.assert_called_once_with([sys.executable, str(mock_root_path/'onlogin.py')])

		run_command.reset_mock()
		self.assertTrue(workstation.onlogout())
		run_command.assert_called_once_with([sys.executable, str(mock_root_path/'onlogout.py')])

		run_command.reset_mock()
		self.assertTrue(workstation.onlock())
		run_command.assert_called_once_with([sys.executable, str(mock_root_path/'onlock.py')])

		run_command.reset_mock()
		self.assertTrue(workstation.onunlock())
		run_command.assert_called_once_with([sys.executable, str(mock_root_path/'onunlock.py')])
