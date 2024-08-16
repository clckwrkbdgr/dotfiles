import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'
import os, sys, tempfile
BUILTIN_OPEN = 'builtins.open' if sys.version_info[0] >= 3 else '__builtin__.open'
from ..savefile import Savefile, AutoSavefile

class TestAutoSavefile(unittest.TestCase):
	def should_save_autosavefile_if_ok(self):
		mock_savefile = mock.MagicMock()
		mock_savefile.load.return_value = 'mock_reader'
		mock_savefile.save.return_value.__enter__.return_value = 'mock_writer'
		with AutoSavefile(mock_savefile) as savefile:
			obj = mock.MagicMock()
			self.assertEqual(savefile.reader, 'mock_reader')
			savefile.save(obj, 'version')
		obj.save.assert_called_with('mock_writer')
		mock_savefile.save.assert_called_with('version')
	def should_not_save_autosavefile_if_not_ok(self):
		mock_savefile = mock.MagicMock()
		mock_savefile.load.return_value = 'mock_reader'
		mock_savefile.save.return_value.__enter__.return_value = 'mock_writer'
		with AutoSavefile(mock_savefile) as savefile:
			obj = mock.MagicMock()
			self.assertEqual(savefile.reader, 'mock_reader')
		obj.save.assert_not_called()
		mock_savefile.save.assert_not_called()
		mock_savefile.unlink.assert_called_with()

class TestSavefile(unittest.TestCase):
	@mock.patch('os.stat')
	@mock.patch('os.path.exists', side_effect=[False, True])
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_get_last_save_time(self, mock_filename, os_path_exists, os_stat):
		os_stat.return_value.st_mtime = 123
		self.assertEqual(Savefile.last_save_time(), 0)
		self.assertEqual(Savefile.last_save_time(), 123)
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_load_game_from_non_existent_file(self, mock_filename, os_path_exists):
		savefile = Savefile()
		self.assertEqual(savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		reader = savefile.load()
		self.assertEqual(reader, None)
	@mock.patch('os.path.exists', side_effect=[True])
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_load_game_from_file_if_exists(self, mock_filename, os_path_exists):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		VERSION = 666
		stream = mock.mock_open(read_data='{version}\x00123\x00game data'.format(version=VERSION))
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile()
			reader = savefile.load()
			self.assertEqual(reader.version, VERSION)
			game_object = (int(reader.read()), reader.read())
			self.assertEqual(game_object, (123, 'game data'))
			stream.assert_called_once_with(Savefile.FILENAME, 'r')
			handle = stream()
			handle.read.assert_called_once()
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_save_game_to_file(self, mock_filename):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		stream = mock.mock_open()
		VERSION = 666
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile()
			with savefile.save(VERSION) as writer:
				writer.write(123)
				writer.write('game data')

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
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_unlink_savefile_on_crash_during_saving(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		stream = mock.mock_open()
		VERSION = 666
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile()
			try:
				with savefile.save(VERSION) as writer:
					writer.write(123)
					raise RuntimeError('crash!')
			except RuntimeError as e:
				self.assertEqual(str(e), 'crash!')

			stream.assert_called_once_with(Savefile.FILENAME, 'w')
			handle = stream()
			handle.write.assert_has_calls([
				mock.call('{0}'.format(666)),
				mock.call('\x00'),
				mock.call('123'),
				])
			os_unlink.assert_called_once_with(Savefile.FILENAME)
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[True])
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_unlink_save_file_if_exists(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		savefile = Savefile()
		savefile.unlink()
		os_unlink.assert_called_once_with(Savefile.FILENAME)
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[False])
	@mock.patch('src.system.savefile.Savefile.FILENAME', new_callable=mock.PropertyMock, return_value=os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
	def should_not_unlink_save_file_if_does_not_exist(self, mock_filename, os_path_exists, os_unlink):
		self.assertEqual(Savefile.FILENAME, os.path.join(tempfile.gettempdir(), "dotrogue_unittest.sav"))
		savefile = Savefile()
		savefile.unlink()
		os_unlink.assert_not_called()
