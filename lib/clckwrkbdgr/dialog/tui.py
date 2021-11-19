import os, sys, subprocess
import six
from . import _base

def message(text): # pragma: no cover -- TODO
	width, height = int(subprocess.check_output(['tput', 'cols']).decode()), int(subprocess.check_output(['tput', 'lines']).decode())
	height -= 2
	return 0 == subprocess.call(['whiptail', '--msgbox', text, str(height), str(width)])

def choice(items, prompt=None): # pragma: no cover -- TODO
	items = _base.make_choices(items)
	item_keys = _base.get_choices_map(items)

	menu = []
	for item in items:
		if item.key:
			menu.extend((item.key, item.text))
		else:
			menu.extend((item.index, item.text))

	width, height = int(subprocess.check_output(['tput', 'cols']).decode()), int(subprocess.check_output(['tput', 'lines']).decode())
	height -= 2
	whiptail = subprocess.Popen(['whiptail', '--notags', '--menu', str(prompt or ''), str(height), str(width), str(len(items)), '--'] + list(map(str, menu)), stderr=subprocess.PIPE)
	_, stderr = whiptail.communicate()
	whiptail.wait()

	if not stderr:
		return None
	key = stderr.decode('utf-8', 'replace')
	result = _base.find_choice_in_map(item_keys, key)
	return result
