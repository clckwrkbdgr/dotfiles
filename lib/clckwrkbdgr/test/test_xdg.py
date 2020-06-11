import unittest
from unittest import mock
unittest.defaultTestLoader.testMethodPrefix = 'should'
import clckwrkbdgr.xdg as xdg

class TestXDGUtils(unittest.TestCase):
	@mock.patch('pathlib.Path.mkdir')
	def should_create_subdir_for_config_path(self, mkdir_mock):
		self.assertEqual(xdg.save_config_path('test_xdg'), xdg.XDG_CONFIG_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch('pathlib.Path.mkdir')
	def should_create_subdir_for_data_path(self, mkdir_mock):
		self.assertEqual(xdg.save_data_path('test_xdg'), xdg.XDG_DATA_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch('pathlib.Path.mkdir')
	def should_create_subdir_for_cache_path(self, mkdir_mock):
		self.assertEqual(xdg.save_cache_path('test_xdg'), xdg.XDG_CACHE_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch('pathlib.Path.mkdir')
	def should_create_subdir_for_state_path(self, mkdir_mock):
		self.assertEqual(xdg.save_state_path('test_xdg'), xdg.XDG_STATE_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
