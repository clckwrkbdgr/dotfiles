import os, sys, subprocess
import six

def choice(items, prompt=None): # pragma: no cover -- TODO
	item_keys = {}
	menu = []
	for index, item in enumerate(items):
		if isinstance(item, six.string_types):
			item = (index, item)
		menu.extend(item)
	zenity = subprocess.Popen(['zenity', '--list', '--text', str(prompt or ''), '--column', 'key', '--column', 'value', '--print-column', '1', '--hide-column', '1', '--hide-header'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	choice, _ = zenity.communicate('\n'.join(map(str, menu)).encode('utf-8', 'replace'))
	zenity.wait()
	if not choice:
		return None
	return choice.decode('utf-8', 'replace').rstrip('\n')
