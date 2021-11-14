import os, sys, subprocess
import six

def choice(items, prompt=None): # pragma: no cover -- TODO
	item_keys = {}
	menu = []
	for index, item in enumerate(items):
		if isinstance(item, six.string_types):
			item = (index, item)
		menu.extend(item)
	width, height = int(subprocess.check_output(['tput', 'cols']).decode()), int(subprocess.check_output(['tput', 'lines']).decode())
	height -= 2
	whiptail = subprocess.Popen(['whiptail', '--notags', '--menu', str(prompt or ''), str(height), str(width), str(len(items)), '--'] + list(map(str, menu)), stderr=subprocess.PIPE)
	_, stderr = whiptail.communicate()
	whiptail.wait()
	if not stderr:
		return None
	return stderr.decode('utf-8', 'replace')
