#!/usr/bin/env python
import sys, re, subprocess
if sys.argv[1:] == ['clean']:
	in_diff_category = False
	for line in sys.stdin.read().splitlines():
		if line == '[diff]':
			in_diff_category = True
		elif in_diff_category:
			if line.startswith('['):
				in_diff_category = False
			else:
				line = re.sub(r'^(\s+submodule\s*=\s*)diff\s*$', r'\1{DIFF}', line)
		print(line)
	sys.exit()

def try_int(value):
	try:
		return int(value)
	except:
		return value

result_value = 'log'
try:
	output = subprocess.check_output(["git", "--version"], stderr=subprocess.STDOUT)
	output = output.decode('utf-8', 'replace').splitlines()[0]
	version = re.search(r'git version (\d\S+)\s*$$', output).group(1)
	version = tuple(map(try_int, version.split('.')))
	if version > (2, 0):
		result_value = 'diff'
except subprocess.CalledProcessError as e:
	pass
except:
	import traceback
	traceback.print_exc()

target_line = re.compile(r'^([ \t]*submodule = ){DIFF}$')
for line in sys.stdin.read().splitlines():
	m = target_line.match(line)
	if m:
		print(m.group(1) + result_value)
	else:
		print(line)
