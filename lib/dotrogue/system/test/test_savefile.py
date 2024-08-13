import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
import os, sys, tempfile
BUILTIN_OPEN = 'builtins.open' if sys.version_info[0] >= 3 else '__builtin__.open'
from ..savefile import Savefile

class TestSavefile(unittest.TestCase):
	@mock.patch('os.stat')
	@mock.patch('os.path.exists', side_effect=[False, True])
	@mock.patch('dotrogue.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_get_last_save_time(self, mock_filename, os_path_exists, os_stat):
		os_stat.return_value.st_mtime = 123
		self.assertEqual(Savefile.last_save_time(), 0)
		self.assertEqual(Savefile.last_save_time(), 123)
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('dotrogue.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_load_game_from_non_existent_file(self, mock_filename, os_path_exists):
		savefile = Savefile()
		self.assertEqual(savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		mock_loader_function = mock.MagicMock()
		result = savefile.load(mock_loader_function)
		mock_loader_function.assert_not_called()
		self.assertEqual(result, None)
	@mock.patch('os.path.exists', side_effect=[True])
	@mock.patch('dotrogue.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_load_game_from_file_if_exists(self, mock_filename, os_path_exists):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		VERSION = 666
		stream = mock.mock_open(read_data='{version}\x00123\x00game data'.format(version=VERSION))
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile()
			def _mock_loader_function(data):
				self.assertEqual(next(data), str(VERSION))
				return (int(next(data)), next(data))
			game_object = savefile.load(_mock_loader_function)
			self.assertEqual(game_object, (123, 'game data'))
			stream.assert_called_once_with(Savefile.FILENAME, 'r')
			handle = stream()
			handle.read.assert_called_once()
	@mock.patch('dotrogue.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_save_game_to_file(self, mock_filename):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		stream = mock.mock_open()
		VERSION = 666
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile()
			def _mock_saver():
				yield VERSION
				yield 123
				yield 'game data'
			savefile.save(_mock_saver)

			stream.assert_called_once_with(Savefile.FILENAME, 'w')
			handle = stream()
			handle.write.assert_has_calls([
				mock.call('{0}'.format(666)),
				mock.call('\x00'),
				mock.call('123'),
				mock.call('\x00'),
				mock.call('game data'),
				])
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[True])
	@mock.patch('dotrogue.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_unlink_save_file_if_exists(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		savefile = Savefile()
		savefile.unlink()
		os_unlink.assert_called_once_with(Savefile.FILENAME)
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('dotrogue.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_unlink_save_file_if_does_not_exist(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		savefile = Savefile()
		savefile.unlink()
		os_unlink.assert_not_called()
