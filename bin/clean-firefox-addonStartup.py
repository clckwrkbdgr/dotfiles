#!/usr/bin/python
import os, sys, io
import json
from clckwrkbdgr import firefox

def process_recursively(subtree, key_name, new_value, skip_if=None):
	""" Processes value with given key in the subtree.
	If new_value is None, removes key from tree, otherwise replaces old value with the new one.
	If skip_if is specified, it should be function(value) that returns True if this specific value should not be touched.
	Continues recursively for internal subtrees.
	"""
	for subkey in list(subtree.keys()):
		if subkey == key_name:
			if skip_if is not None and skip_if(subtree[subkey]):
				continue
			if new_value is None:
				del subtree[subkey]
			else:
				subtree[subkey] = new_value
		elif isinstance(subtree[subkey], dict):
			process_recursively(subtree[subkey], key_name, new_value, skip_if=skip_if)

# Parsing.
bin_stdin = io.open(sys.stdin.fileno(), 'rb')
data = firefox.decompress_mozLz4(bin_stdin.read())
tree = json.loads(data.decode('utf-8'))
if 'app-system-addons' in tree:
	del tree['app-system-addons']

# Staged addons.
tree = {
		key:{
			subkey:subvalue
			for subkey, subvalue in subtree.items()
			if subkey != "staged"
			}
		for key,subtree in tree.items()
		}

# Cleaning cache/state values.
for addon in tree["app-global"]["addons"].values():
	addon["startupData"]["chromeEntries"].sort()
process_recursively(tree, 'telemetryKey', None)
process_recursively(tree, 'signedDate', None)
process_recursively(tree, 'signedState', None)
process_recursively(tree, 'lastModifiedTime', 0)
process_recursively(tree, 'version', "0.0")
process_recursively(tree, 'path', None, skip_if=lambda v: v is not None)

# Built-in addons.
if "proxy-failover@mozilla.com" in tree["app-system-defaults"]["addons"]:
	del tree["app-system-defaults"]["addons"]["proxy-failover@mozilla.com"]

# Cleaning artefacts left after addon update or preparation to update.
for addon in tree["app-profile"]["addons"].values():
	if 'startupData' not in addon:
		continue
	for listeners in addon['startupData'].get('persistentListeners', {}).get('webRequest', {}).values():
		listeners.clear()

# Finalization and dumping.
result = json.dumps(tree, indent=4, sort_keys=True)
result = result.replace(os.environ['HOME'], '$HOME')
print(result)
