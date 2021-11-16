import os, sys, subprocess
import six
from . import _base

def choice(items, prompt=None): # pragma: no cover -- TODO
	items = _base.make_choices(items)
	item_keys = _base.get_choices_map(items)

	menu = []
	for item in items:
		if item.key:
			menu.extend((item.key, item.text))
		else:
			menu.extend((item.index, item.text))

	zenity = subprocess.Popen(['zenity', '--list', '--text', str(prompt or ''), '--column', 'key', '--column', 'value', '--print-column', '1', '--hide-column', '1', '--hide-header'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	choice, _ = zenity.communicate('\n'.join(map(str, menu)).encode('utf-8', 'replace'))
	zenity.wait()

	if not choice:
		return None
	key = choice.decode('utf-8', 'replace').rstrip('\n')
	result = _base.find_choice_in_map(item_keys, key)
	return result
