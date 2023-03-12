import time
import io
import logging
try:
	from pathlib2 import Path
except: # pragma: no cover
	from pathlib import Path
from clckwrkbdgr import unittest
import clckwrkbdgr.logging
from clckwrkbdgr.logging import init

class TestBasicLogger(unittest.TestCase):
	def should_print_message_to_stream(self):
		with io.StringIO() as stream:
			logger = init('should_print_message_to_stream', stream=stream)
			logger.warning(u'Hello world!')
			logger.info(u'Info.')
			logger.debug(u'Debug...')
			self.assertEqual(stream.getvalue(), '[WARNING] should_print_message_to_stream: Hello world!\n')
	def should_print_message_to_stream_using_root_logger(self):
		for _handler in logging.root.handlers[:]: # pragma: no cover
			logging.root.removeHandler(_handler)
		with io.StringIO() as stream:
			logger = init('should_print_message_to_stream_using_root_logger', stream=stream)
			logging.warning(u'I am root!')
			self.assertEqual(stream.getvalue(), '[WARNING] root: I am root!\n')
	def should_reinit_logger(self):
		with io.StringIO() as stream:
			logger = init('should_reinit_logger', stream=stream)
			logger.warning(u'Reinit logger!')
			logger = init('should_reinit_logger', stream=stream)
			logger.warning(u'Reinit logger!')
			self.assertEqual(stream.getvalue(), '[WARNING] should_reinit_logger: Reinit logger!\n' * 2)
	def should_init_already_requested_logger(self):
		logger = logging.getLogger('should_init_already_requested_logger')
		with io.StringIO() as stream:
			logger = init(logger, stream=stream)
			logger.warning(u'Redefine logger!')
			self.assertEqual(stream.getvalue(), '[WARNING] should_init_already_requested_logger: Redefine logger!\n')
	def should_create_verbose_logger(self):
		with io.StringIO() as stream:
			logger = init('should_create_verbose_logger', verbose=True, stream=stream)
			logger.warning(u'Warning!')
			logger.info(u'Info.')
			logger.debug(u'Debug...')
			self.assertEqual(stream.getvalue(),
					'[WARNING] should_create_verbose_logger: Warning!\n'
					'[INFO] should_create_verbose_logger: Info.\n'
					)
	def should_create_debug_logger(self):
		with io.StringIO() as stream:
			logger = init('should_create_debug_logger', verbose=False, debug=True, stream=stream)
			logger.warning(u'Warning!')
			logger.info(u'Info.')
			logger.debug(u'Debug...')
			self.assertEqual(stream.getvalue(),
					'[WARNING] should_create_debug_logger: Warning!\n'
					'[INFO] should_create_debug_logger: Info.\n'
					'[DEBUG] should_create_debug_logger: Debug...\n'
					)

class TestFileLogger(unittest.fs.TestCase):
	MODULES = [clckwrkbdgr.logging]
	@unittest.mock.patch('logging.Formatter.converter', side_effect=[time.gmtime(10000)])
	def should_print_message_to_file_and_stream(self, time_localtime):
		logfile = Path('/trace.log')
		with io.StringIO() as stream:
			logger = init('should_print_message_to_file_and_stream', stream=stream, filename=logfile)
			logger.warning(u'File and stream!')
			self.assertEqual(stream.getvalue(), '[WARNING] should_print_message_to_file_and_stream: File and stream!\n')
		self.assertEqual(logfile.read_text(), '1970-01-01 02:46:40:should_print_message_to_file_and_stream:WARNING: File and stream!\n')
	@unittest.mock.patch('logging.Formatter.converter', side_effect=[time.gmtime(10000)])
	def should_print_message_to_file_only(self, time_localtime):
		logfile = Path('/trace.log')
		logger = init('should_print_message_to_file_and_stream', stream=None, filename=logfile)
		logger.warning(u'File only!')
		self.assertEqual(logfile.read_text(), '1970-01-01 02:46:40:should_print_message_to_file_and_stream:WARNING: File only!\n')
