import os, sys, re
from clckwrkbdgr.pyshell import sh

""" Script to wrap MSVS commands (like CL, LINK etc).
It uses vsvarsall.bat scripts from MSVS distribution.

Usage:
	vcvarsall.py [-<VSversion>] <command> <args...>

Optional VS version is treated as major of semver (not year),
e.g. 11 (2012), 14 (2019).
"""

args = sys.argv[1:]
vs_version = None
if args and args[0].startswith('-'):
	vs_version = args[0][1:]
	args = args[1:]

root = r'C:\Program Files (x86)'
MSVSDIR = re.compile(r'Microsoft Visual Studio *(\d+)(?:[.]\d+)?')
found = {}
for entry in os.listdir(root):
	m = MSVSDIR.match(entry)
	if not m:
		continue
	if os.path.isdir(os.path.join(root, entry, 'VC')):
		found[int(m.group(1))] = os.path.join(root, entry, 'VC')
if not vs_version:
	batch_file_dir = sorted(found.items(), key=lambda _:_[0])[-1][-1]
else:
	batch_file_dir = found[int(vs_version)]

original_dir = os.getcwd()
os.chdir(batch_file_dir)
vsenv = sh(sh['COMSPEC'], '/C', 'vcvarsall.bat x86 && SET', stdout=str)
os.chdir(original_dir)

vsenv = dict([line.rstrip('\n').split('=', 1) for line in vsenv.splitlines()])
if not vsenv:
	print("Error: {0}\\vsvarsall.bat did not set environment!".format(batch_file_dir))
	sh.exit(1)
os.environ.update(vsenv)

sh(args)
