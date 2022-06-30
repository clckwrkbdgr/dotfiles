from clckwrkbdgr import unittest
from clckwrkbdgr.unittest import mock
import tempfile
try: # pragma: no cover
	from pathlib2 import Path
	_pathlib = 'pathlib2'
except ImportError: # pragma: no cover
	from pathlib import Path
	_pathlib = 'pathlib'
import clckwrkbdgr.xdg as xdg

class TestXDGUtils(unittest.TestCase):
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_path(self, mkdir_mock):
		XDG_TMP = Path(tempfile.gettempdir())
		self.assertEqual(xdg._save_XDG_path(XDG_TMP, 'test_base_xdg'), XDG_TMP/'test_base_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_path_with_multiple_parts(self, mkdir_mock):
		XDG_TMP = Path(tempfile.gettempdir())
		self.assertEqual(xdg._save_XDG_path(XDG_TMP, 'test_xdg', 'subdir'), XDG_TMP/'test_xdg'/'subdir')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_cache_subdir_path(self, mkdir_mock):
		XDG_TMP = Path(tempfile.gettempdir())
		self.assertEqual(xdg._save_XDG_path(XDG_TMP, 'test_xdg_cached'), XDG_TMP/'test_xdg_cached')
		self.assertEqual(xdg._save_XDG_path(XDG_TMP, 'test_xdg_cached'), XDG_TMP/'test_xdg_cached')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_for_config_path(self, mkdir_mock):
		self.assertEqual(xdg.save_config_path('test_xdg'), xdg.XDG_CONFIG_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_for_data_path(self, mkdir_mock):
		self.assertEqual(xdg.save_data_path('test_xdg'), xdg.XDG_DATA_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_for_cache_path(self, mkdir_mock):
		self.assertEqual(xdg.save_cache_path('test_xdg'), xdg.XDG_CACHE_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_for_state_path(self, mkdir_mock):
		self.assertEqual(xdg.save_state_path('test_xdg'), xdg.XDG_STATE_HOME/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
	@mock.patch(_pathlib+'.Path.mkdir')
	def should_create_subdir_for_runtime_path(self, mkdir_mock):
		self.assertEqual(xdg.save_runtime_path('test_xdg'), xdg.XDG_RUNTIME_DIR/'test_xdg')
		mkdir_mock.assert_called_once_with(parents=True, exist_ok=True)
