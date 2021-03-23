#!/usr/bin/python
import os, sys, io
import json
from clckwrkbdgr import firefox

def process_recursively(subtree, key_name, new_value, skip_if=None):
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

bin_stdin = io.open(sys.stdin.fileno(), 'rb')
data = firefox.decompress_mozLz4(bin_stdin.read())
tree = json.loads(data.decode('utf-8'))

tree = {
		key:{
			subkey:subvalue
			for subkey, subvalue in subtree.items()
			if subkey != "staged"
			}
		for key,subtree in tree.items()
		}
for addon in tree["app-global"]["addons"].values():
	addon["startupData"]["chromeEntries"].sort()
process_recursively(tree, 'telemetryKey', None)
process_recursively(tree, 'signedDate', None)
process_recursively(tree, 'signedState', None)
process_recursively(tree, 'lastModifiedTime', 0)
process_recursively(tree, 'version', "0.0")
process_recursively(tree, 'path', None, skip_if=lambda v: v is not None)

# sed 's/\\(\"lastModifiedTime\"\\)[^,]*\\(,\\?\\)$/\\1: 0\\2/;s/\\(\"version\"\\):[^,]*\\(,\\?\\)$/\\1: \"0.0\"\\2/'
# sed '/^ *\"path\": null,$/d'
# sed 's|'\"$HOME\"'|$HOME|g'"

result = json.dumps(tree, indent=4, sort_keys=True)
result = result.replace(os.environ['HOME'], '$HOME')
print(result)
