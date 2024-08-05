import sys
from .. import messages
import datetime
import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	import unittest.mock as mock
except ImportError: # pragma: no cover
	import mock
mock.patch.TEST_PREFIX = 'should'

BUILTIN_OPEN = 'builtins.open' if sys.version_info[0] >= 3 else '__builtin__.open'

class TestLogger(unittest.TestCase):
	@mock.patch('datetime.datetime', wraps=datetime.datetime)
	def should_log_messages(self, datetime_datetime):
		datetime_datetime.now.return_value = datetime.datetime(2020, 12, 31, 12, 34, 56)
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.init('test.log')
			logger.log('info', 'foo bar')
		stream.assert_called_once_with('test.log', 'w')
		handle = stream()
		handle.write.assert_called_once_with('2020-12-31T12:34:56:info: foo bar\n')
	@mock.patch('datetime.datetime', wraps=datetime.datetime)
	def should_reopen_log_file(self, datetime_datetime):
		datetime_datetime.now.return_value = datetime.datetime(2020, 12, 31, 12, 34, 56)
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.init('test.log')
			logger.init('test2.log')
			logger.log('info', 'foo bar')
		stream.assert_called_with('test2.log', 'w')
		handle = stream()
		handle.write.assert_called_once_with('2020-12-31T12:34:56:info: foo bar\n')
	def should_not_log_is_file_is_not_opened(self):
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.log('info', 'foo bar')
		stream.assert_not_called()
		handle = stream()
		handle.write.assert_not_called()
	@mock.patch('datetime.datetime', wraps=datetime.datetime)
	def should_log_debug_messages(self, datetime_datetime):
		datetime_datetime.now.return_value = datetime.datetime(2020, 12, 31, 12, 34, 56)
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.init('test.log')
			logger.debug('foo bar')
		stream.assert_called_once_with('test.log', 'w')
		handle = stream()
		handle.write.assert_called_once_with('2020-12-31T12:34:56:debug: foo bar\n')
	@mock.patch('datetime.datetime', wraps=datetime.datetime)
	def should_log_info_messages(self, datetime_datetime):
		datetime_datetime.now.return_value = datetime.datetime(2020, 12, 31, 12, 34, 56)
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.init('test.log')
			logger.info('foo bar')
		stream.assert_called_once_with('test.log', 'w')
		handle = stream()
		handle.write.assert_called_once_with('2020-12-31T12:34:56:info: foo bar\n')
	@mock.patch('datetime.datetime', wraps=datetime.datetime)
	def should_log_warning_messages(self, datetime_datetime):
		datetime_datetime.now.return_value = datetime.datetime(2020, 12, 31, 12, 34, 56)
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.init('test.log')
			logger.warning('foo bar')
		stream.assert_called_once_with('test.log', 'w')
		handle = stream()
		handle.write.assert_called_once_with('2020-12-31T12:34:56:warning: foo bar\n')
	@mock.patch('datetime.datetime', wraps=datetime.datetime)
	def should_log_error_messages(self, datetime_datetime):
		datetime_datetime.now.return_value = datetime.datetime(2020, 12, 31, 12, 34, 56)
		stream = mock.mock_open()
		with mock.patch(BUILTIN_OPEN, stream):
			logger = messages.Logger()
			logger.init('test.log')
			logger.error('foo bar')
		stream.assert_called_once_with('test.log', 'w')
		handle = stream()
		handle.write.assert_called_once_with('2020-12-31T12:34:56:error: foo bar\n')

class TestEvents(unittest.TestCase):
	def should_str_events(self):
		self.assertEqual(str(messages.DiscoverEvent('@')), 'Discovered @')
		self.assertEqual(str(messages.AttackEvent('@', 'M')), '@ attacks M')
		self.assertEqual(str(messages.HealthEvent('@', -10)), '@ -10 hp')
		self.assertEqual(str(messages.HealthEvent('@', +10)), '@ +10 hp')
		self.assertEqual(str(messages.DeathEvent('@')), '@ dies')
		self.assertEqual(str(messages.MoveEvent('@', 'POS')), '@ moves to POS')
		self.assertEqual(str(messages.BumpEvent('@', 'POS')), '@ bumps into POS')
