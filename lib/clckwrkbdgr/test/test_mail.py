import subprocess
from .. import unittest
from .. import mail
from .. import xdg
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

class TestProviderQueue(unittest.TestCase):
	class MockPreferred(mail.Provider):
		def __init__(self):
			self.data = {}
		@classmethod
		def qualify(cls): return True
		def send(self, subject, body, payload=None):
			self.data = {'subject': subject, 'body': body, 'payload': payload}
	class MockPreferredButUnavailable(mail.Provider):
		@classmethod
		def qualify(cls): return False
	class MockLeftover(mail.Provider): # pragma: no cover -- search order doesn't get to it at all.
		@classmethod
		def qualify(cls): return True

	def should_register_providers(self):
		with unittest.mock.patch.object(mail.Provider, '_providers', []) as _providers:
			mail.Provider.register(0.5)(self.MockPreferred)
			mail.Provider.register(0.1)(self.MockLeftover)
			self.assertEqual(mail.Provider._providers, [
				(0.5, self.MockPreferred),
				(0.1, self.MockLeftover),
				])
	def should_pick_provider_with_topmost_priority(self):
		with unittest.mock.patch.object(mail.Provider, '_providers', []) as _providers:
			with unittest.mock.patch.object(mail.Provider, '_current', None) as _providers:
				mail.Provider.register(0.1)(self.MockLeftover)
				mail.Provider.register(0.5)(self.MockPreferred)
				self.assertIsNone(mail.Provider._current)
				self.assertEqual(type(mail.Provider.current()), self.MockPreferred)
				self.assertEqual(type(mail.Provider._current), self.MockPreferred)
	def should_pick_only_providers_which_are_available(self):
		with unittest.mock.patch.object(mail.Provider, '_providers', []) as _providers:
			with unittest.mock.patch.object(mail.Provider, '_current', None) as _providers:
				mail.Provider.register(0.1)(self.MockLeftover)
				mail.Provider.register(0.5)(self.MockPreferred)
				mail.Provider.register(1.0)(self.MockPreferredButUnavailable)
				self.assertIsNone(mail.Provider._current)
				self.assertEqual(type(mail.Provider.current()), self.MockPreferred)
				self.assertEqual(type(mail.Provider._current), self.MockPreferred)

	def should_send_message_using_default_provider(self):
		with unittest.mock.patch.object(mail.Provider, '_providers', []) as _providers:
			with unittest.mock.patch.object(mail.Provider, '_current', None) as _providers:
				mail.Provider.register(0.5)(self.MockPreferred)
				mail.send('hello', 'world', {'attach': 'data'})
				self.assertEqual(mail.Provider.current().data, {
					'subject': 'hello',
					'body': 'world',
					'payload': {'attach': 'data'},
					})

class TestDesktopFileProvider(unittest.fs.TestCase):
	MODULES = [mail]
	def should_always_qualify(self):
		self.assertTrue(mail.DesktopFile.qualify())
	def should_create_desktop_file_with_attachments(self):
		self.fs.create_dir('/destdir')
		self.assertTrue(mail.DesktopFile('/destdir').send('name', u'body', payload={
			'attach.sh': u'data',
			}))
		self.assertEqual(Path('/destdir/name').read_text(), 'body')
		self.assertEqual(Path('/destdir/attach.sh').read_text(), 'data')


try: # pragma: no cover -- py2 has no shutil.which
	from shutil import which
	WHICH_MOCK_NAME = 'shutil.which'
except: # pragma: no cover -- py2 has no shutil.which
	WHICH_MOCK_NAME = 'clckwrkbdgr.pyshell.which'

class TestMailXProvider(unittest.TestCase):
	@unittest.mock.patch(WHICH_MOCK_NAME, side_effect=[None, 'ok'])
	def should_always_qualify(self, shutil_which):
		self.assertFalse(mail.MailX.qualify())
		self.assertTrue(mail.MailX.qualify())
	@unittest.mock.patch('getpass.getuser', side_effect=['me'])
	@unittest.mock.patch('subprocess.Popen')
	def should_create_desktop_file_with_attachments(self, subprocess_Popen, getpass_getuser):
		mock_process = unittest.mock.Mock()
		mock_process.configure_mock(**({'wait.side_effect':[0]}))
		subprocess_Popen.side_effect = [mock_process]

		self.assertTrue(mail.MailX().send('name', u'body'))
		subprocess_Popen.assert_has_calls([
			unittest.mock.call(['mail', '-s', 'name', 'me'], stdin=subprocess.PIPE),
			])
		mock_process.assert_has_calls([
			unittest.mock.call.communicate(b'body'),
			unittest.mock.call.wait(),
			])
