# -*- coding: utf-8 -*-
import subprocess
from .. import unittest
from .. import commands

class TestCommandShortcuts(unittest.TestCase):
	@unittest.mock.patch('subprocess.call', side_effect=[0, 1])
	def should_run_simple_commands(self, subprocess_call):
		self.assertEqual(commands.run(['badger_test_command', 'arg1', '--option', 'value']), 0)
		self.assertEqual(commands.run(['badger_test_command', 'arg1', '--option', 'value']), 1)
		subprocess_call.assert_has_calls([
			unittest.mock.call(['badger_test_command', 'arg1', '--option', 'value']),
			unittest.mock.call(['badger_test_command', 'arg1', '--option', 'value']),
			])
	@unittest.mock.patch('subprocess.call', side_effect=[0, 1])
	def should_run_quiet_commands(self, subprocess_call):
		self.assertEqual(commands.run_quiet(['badger_quiet_test_command', 'arg1', '--option', 'value']), 0)
		self.assertEqual(commands.run_quiet(['badger_quiet_test_command', 'arg1', '--option', 'value']), 1)
		subprocess_call.assert_has_calls([
			unittest.mock.call(['badger_quiet_test_command', 'arg1', '--option', 'value'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
			unittest.mock.call(['badger_quiet_test_command', 'arg1', '--option', 'value'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
			])
	@unittest.mock.patch('subprocess.Popen', side_effect=['foo', 'bar'])
	def should_run_detached_commands(self, subprocess_Popen):
		self.assertEqual(commands.run_detached(['badger_background_test_command', 'arg1', '--option', 'value']), 'foo')
		self.assertEqual(commands.run_detached(['badger_background_test_command', 'arg1', '--option', 'value']), 'bar')
		subprocess_Popen.assert_has_calls([
			unittest.mock.call(['badger_background_test_command', 'arg1', '--option', 'value'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
			unittest.mock.call(['badger_background_test_command', 'arg1', '--option', 'value'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
			])
	@unittest.mock.patch('subprocess.Popen', side_effect=['foo', 'bar'])
	def should_run_detached_commands_in_external_terminal(self, subprocess_Popen):
		self.assertEqual(commands.run_terminal(['badger_background_test_command', 'arg1', '--option', 'value']), 'foo')
		self.assertEqual(commands.run_terminal(['badger_background_test_command', 'arg1', '--option', 'value']), 'bar')
		subprocess_Popen.assert_has_calls([
			unittest.mock.call(['urxvt', '-e', 'badger_background_test_command', 'arg1', '--option', 'value'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
			unittest.mock.call(['urxvt', '-e', 'badger_background_test_command', 'arg1', '--option', 'value'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
			])
	@unittest.mock.patch('subprocess.check_output', side_effect=[b'success', subprocess.CalledProcessError(0, '<cmd>', u'помилка'.encode('cp1251'))])
	def should_get_output_from_command(self, subprocess_check_output):
		self.assertEqual(commands.get_output(['badger_test_command', 'arg1', '--option', 'value']), 'success')
		self.assertEqual(commands.get_output(['badger_test_command', 'arg1', '--option', 'value'], encoding='cp1251'), u'помилка')
		subprocess_check_output.assert_has_calls([
			unittest.mock.call(['badger_test_command', 'arg1', '--option', 'value']),
			unittest.mock.call(['badger_test_command', 'arg1', '--option', 'value']),
			])
	def should_pipe_input_and_get_output_from_command(self):
		with unittest.mock.patch('subprocess.Popen') as subprocess_Popen:
			subprocess_Popen().wait.side_effect = [0]
			subprocess_Popen().communicate.side_effect = [(b'success', None)]
			self.assertEqual(commands.pipe(['badger_test_command', 'arg1', '--option', 'value'], 'input'), 'success')
			subprocess_Popen.assert_has_calls([
				unittest.mock.call(),
				unittest.mock.call(),
				unittest.mock.call(['badger_test_command', 'arg1', '--option', 'value'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT),
				unittest.mock.call().communicate(b'input'),
				unittest.mock.call().wait(),
				])

		with unittest.mock.patch('subprocess.Popen') as subprocess_Popen:
			subprocess_Popen().wait.side_effect = [1]
			subprocess_Popen().communicate.side_effect = [(u'помилка'.encode('cp1251'), None)]
			self.assertEqual(commands.pipe(['badger_test_command', 'arg1', '--option', 'value'], u'ввід', encoding='cp1251'), u'помилка')
			subprocess_Popen.assert_has_calls([
				unittest.mock.call(),
				unittest.mock.call(),
				unittest.mock.call(['badger_test_command', 'arg1', '--option', 'value'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT),
				unittest.mock.call().communicate(u'ввід'.encode('cp1251')),
				unittest.mock.call().wait(),
				])
