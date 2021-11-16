import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import clckwrkbdgr.dialog as dialog
import clckwrkbdgr.dialog.cli
import clckwrkbdgr.dialog.tui
import clckwrkbdgr.dialog.gui

class TestChoice(unittest.TestCase):
	def should_make_choice_list(self):
		data = [
				'text',
				('key', ['list']),
				]
		expected = [
				dialog.Choice(0, None, 'text'),
				dialog.Choice(1, 'key', str(['list'])),
				]
		self.assertEqual(dialog.make_choices(data), expected)
	def should_make_choices_mapping(self):
		choices = [
				dialog.Choice(0, None, 'text'),
				dialog.Choice(1, 'key', str(['list'])),
				]
		expected = {
				0 : choices[0],
				1 : choices[1],
				'key' : choices[1],
				}
		self.assertEqual(dialog.get_choices_map(choices), expected)
	def should_find_selected_choice_in_map(self):
		choices = [
				dialog.Choice(0, None, 'text'),
				dialog.Choice(1, 'key', str(['list'])),
				]
		mapping = dialog.get_choices_map(choices)
		self.assertEqual(dialog.find_choice_in_map(mapping, '0'), choices[0])
		self.assertEqual(dialog.find_choice_in_map(mapping, '1'), choices[1])
		self.assertEqual(dialog.find_choice_in_map(mapping, 'key'), choices[1])
		self.assertIsNone(dialog.find_choice_in_map(mapping, 'unknown'))
		self.assertIsNone(dialog.find_choice_in_map(mapping, '2'))
