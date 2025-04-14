from clckwrkbdgr import unittest
from clckwrkbdgr.unittest import mock
import os, sys, tempfile
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
BUILTIN_OPEN = 'builtins.open' if sys.version_info[0] >= 3 else '__builtin__.open'
from ..stream import StreamReader, Writer
from ..stream import Savefile, AutoSavefile
from clckwrkbdgr.math import Point, Size, Matrix

class MockSerializableObject:
	def __init__(self, value, data):
		self.value = value
		self.data = data
	@classmethod
	def load(cls, reader):
		return cls(reader.read_int(), reader.read_str())
	def save(self, writer):
		writer.write(self.value)
		writer.write(self.data)

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

class TestReader(unittest.TestCase):
	def should_read_version(self):
		stream = StringIO('666\x00123')
		reader = StreamReader(stream)
		self.assertEqual(reader.version, 666)
		self.assertEqual(reader.read(), '123')
	def should_read_raw_value(self):
		stream = StringIO('666\x00123\x00game data')
		reader = StreamReader(stream)
		self.assertEqual(reader.read(), '123')
		self.assertEqual(reader.read(), 'game data')
	def should_read_raw_value_from_long_buffer(self):
		stream = StringIO('666\x00123\x00game data' + '0'*4096)
		reader = StreamReader(stream)
		self.assertEqual(reader.read(), '123')
		self.assertEqual(reader.read(), 'game data' + '0'*4096)
	def should_read_custom_types(self):
		stream = StringIO('666\x00123\x00game data')
		reader = StreamReader(stream)
		self.assertEqual(reader.read(int), 123)
		self.assertEqual(reader.read(), 'game data')
	def should_read_custom_serializable_objects(self):
		stream = StringIO('666\x00123\x00game data')
		reader = StreamReader(stream)
		obj = reader.read(MockSerializableObject)
		self.assertTrue(isinstance(obj, MockSerializableObject))
		self.assertEqual(obj.value, 123)
		self.assertEqual(obj.data, 'game data')
	def should_read_int(self):
		stream = StringIO('666\x00123\x00game data')
		reader = StreamReader(stream)
		self.assertEqual(reader.read_int(), 123)
		self.assertEqual(reader.read(), 'game data')
	def should_read_strings(self):
		stream = StringIO('666\x00None\x00game data')
		reader = StreamReader(stream)
		self.assertEqual(reader.read_str(), None)
		self.assertEqual(reader.read_str(), 'game data')
	def should_read_booleans(self):
		stream = StringIO('666\x001\x000')
		reader = StreamReader(stream)
		self.assertEqual(reader.read_bool(), True)
		self.assertEqual(reader.read_bool(), False)
	def should_read_points(self):
		stream = StringIO('666\x00100\x00500')
		reader = StreamReader(stream)
		self.assertEqual(reader.read_point(), Point(100, 500))
	def should_read_sizes(self):
		stream = StringIO('666\x00100\x00500')
		reader = StreamReader(stream)
		self.assertEqual(reader.read_size(), Size(100, 500))
	def should_read_lists(self):
		stream = StringIO('666\x002\x00100\x00500')
		reader = StreamReader(stream)
		self.assertEqual(reader.read_list(), ['100', '500'])
	def should_read_lists_of_custom_objects(self):
		stream = StringIO('666\x002\x00100\x00foo\x00500\x00bar')
		reader = StreamReader(stream)
		result = reader.read_list(MockSerializableObject)
		self.assertEqual(len(result), 2)
		self.assertEqual(result[0].value, 100)
		self.assertEqual(result[0].data, 'foo')
		self.assertEqual(result[1].value, 500)
		self.assertEqual(result[1].data, 'bar')
	def should_read_matrices(self):
		stream = StringIO('666\x003\x002\x000\x000;0\x0010\x001;0\x0020\x002;0\x001\x000;1\x0011\x001;1\x0021\x002;1')
		reader = StreamReader(stream)
		matrix = reader.read_matrix(MockSerializableObject)
		self.assertEqual(matrix.size, Size(3, 2))
		self.assertEqual(matrix.cell((0, 0)).value, 00)
		self.assertEqual(matrix.cell((0, 0)).data, '0;0')
		self.assertEqual(matrix.cell((0, 1)).value,  1)
		self.assertEqual(matrix.cell((0, 1)).data, '0;1')
		self.assertEqual(matrix.cell((1, 0)).value, 10)
		self.assertEqual(matrix.cell((1, 0)).data, '1;0')
		self.assertEqual(matrix.cell((1, 1)).value, 11)
		self.assertEqual(matrix.cell((1, 1)).data, '1;1')
		self.assertEqual(matrix.cell((2, 0)).value, 20)
		self.assertEqual(matrix.cell((2, 0)).data, '2;0')
		self.assertEqual(matrix.cell((2, 1)).value, 21)
		self.assertEqual(matrix.cell((2, 1)).data, '2;1')
	def should_read_optional_objects(self):
		stream = StringIO('666\x001\x00123\x00game data')
		reader = StreamReader(stream)
		obj = reader.read(MockSerializableObject, optional=True)
		self.assertTrue(isinstance(obj, MockSerializableObject))
		self.assertEqual(obj.value, 123)
		self.assertEqual(obj.data, 'game data')

		stream = StringIO('666\x000')
		reader = StreamReader(stream)
		obj = reader.read(MockSerializableObject, optional=True)
		self.assertIsNone(obj)

class TestWriter(unittest.TestCase):
	def should_write_raw_values(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write(123)
		writer.write('game data')
		self.assertEqual(stream.getvalue(), '666\x00123\x00game data')
	def should_write_serializable_objects(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		obj = MockSerializableObject(123, 'game data')
		writer.write(obj)
		self.assertEqual(stream.getvalue(), '666\x00123\x00game data')
	def should_write_bool_values(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write(True)
		writer.write(False)
		self.assertEqual(stream.getvalue(), '666\x001\x000')
	def should_write_points(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write(Point(100, 500))
		self.assertEqual(stream.getvalue(), '666\x00100\x00500')
	def should_write_sizes(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write(Size(100, 500))
		self.assertEqual(stream.getvalue(), '666\x00100\x00500')
	def should_write_lists(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write(['100', '500'])
		self.assertEqual(stream.getvalue(), '666\x002\x00100\x00500')
	def should_write_lists_of_custom_objects(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write([
			MockSerializableObject(100, 'foo'),
			MockSerializableObject(500, 'bar'),
			])
		self.assertEqual(stream.getvalue(), '666\x002\x00100\x00foo\x00500\x00bar')
	def should_write_matrices(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		matrix = Matrix(Size(3, 2), None)
		matrix.set_cell((0, 0), MockSerializableObject(00, '0;0'))
		matrix.set_cell((0, 1), MockSerializableObject( 1, '0;1'))
		matrix.set_cell((1, 0), MockSerializableObject(10, '1;0'))
		matrix.set_cell((1, 1), MockSerializableObject(11, '1;1'))
		matrix.set_cell((2, 0), MockSerializableObject(20, '2;0'))
		matrix.set_cell((2, 1), MockSerializableObject(21, '2;1'))
		writer.write(matrix)
		self.assertEqual(stream.getvalue(), '666\x003\x002\x000\x000;0\x0010\x001;0\x0020\x002;0\x001\x000;1\x0011\x001;1\x0021\x002;1')
	def should_write_optional_objects(self):
		stream = StringIO()
		writer = Writer(stream, 666)
		obj = MockSerializableObject(123, 'game data')
		writer.write(obj, optional=True)
		self.assertEqual(stream.getvalue(), '666\x001\x00123\x00game data')

		stream = StringIO()
		writer = Writer(stream, 666)
		writer.write(None, optional=True)
		self.assertEqual(stream.getvalue(), '666\x000')

class TestSavefile(unittest.TestCase):
	@mock.patch('os.stat')
	@mock.patch('os.path.exists', side_effect=[False, True])
	def should_get_last_save_time(self, os_path_exists, os_stat):
		savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
		os_stat.return_value.st_mtime = 123
		self.assertEqual(savefile.last_save_time(), 0)
		self.assertEqual(savefile.last_save_time(), 123)
	@mock.patch('os.path.exists', side_effect=[False])
	def should_not_load_game_from_non_existent_file(self, os_path_exists):
		savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
		self.assertEqual(savefile.filename, os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
		with savefile.get_reader() as reader:
			self.assertEqual(reader, None)
	@mock.patch('os.path.exists', side_effect=[True])
	def should_load_game_from_file_if_exists(self, os_path_exists):
		VERSION = 666
		stream = mock.mock_open(read_data='{version}\x00123\x00game data'.format(version=VERSION))
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
			with savefile.get_reader() as reader:
				self.assertEqual(reader.version, VERSION)
				game_object = (int(reader.read()), reader.read())
			self.assertEqual(game_object, (123, 'game data'))
			stream.assert_called_once_with(savefile.filename, 'r')
			handle = stream()
			handle.read.assert_has_calls([
				mock.call(StreamReader.CHUNK_SIZE),
				mock.call(StreamReader.CHUNK_SIZE),
				])
	def should_save_game_to_file(self):
		stream = mock.mock_open()
		VERSION = 666
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
			with savefile.save(VERSION) as writer:
				writer.write(123)
				writer.write('game data')

			stream.assert_called_once_with(savefile.filename, 'w')
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
	def should_unlink_savefile_on_crash_during_saving(self, os_path_exists, os_unlink):
		stream = mock.mock_open()
		VERSION = 666
		with mock.patch(BUILTIN_OPEN, stream):
			savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
			try:
				with savefile.save(VERSION) as writer:
					writer.write(123)
					raise RuntimeError('crash!')
			except RuntimeError as e:
				self.assertEqual(str(e), 'crash!')

			stream.assert_called_once_with(savefile.filename, 'w')
			handle = stream()
			handle.write.assert_has_calls([
				mock.call('{0}'.format(666)),
				mock.call('\x00'),
				mock.call('123'),
				])
			os_unlink.assert_called_once_with(savefile.filename)
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[True])
	def should_unlink_save_file_if_exists(self, os_path_exists, os_unlink):
		savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
		savefile.unlink()
		os_unlink.assert_called_once_with(savefile.filename)
	@mock.patch('os.unlink')
	@mock.patch('os.path.exists', side_effect=[False])
	def should_not_unlink_save_file_if_does_not_exist(self, os_path_exists, os_unlink):
		savefile = Savefile(os.path.join(tempfile.gettempdir(), "clckwrkbdgr_serialize_stream_unittest.sav"))
		savefile.unlink()
		os_unlink.assert_not_called()
