from __future__ import print_function
import os, sys, subprocess
import re
import random
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
from clckwrkbdgr import xdg

known_hosts = [
		"8.8.8.8", # Google DNS
		"8.8.4.4", # Google DNS
		]

def read_known_hosts(filename): # pragma: no cover -- TODO generic routine to read such .lst files with hash-comments.
	return [line.split('#')[0].strip()
		for line
		in filename.read_text().splitlines()
		if line.strip() and not line.lstrip().startswith('#')
		]

custom_hosts_files = [
		xdg.XDG_DATA_HOME/'known_hosts.lst',
		Path('~/.local/known_hosts.lst').expanduser(),
		]
for filename in custom_hosts_files: # pragma: no cover -- TODO generic routine to read such .lst files with hash-comments.
	if filename.is_file():
		known_hosts.extend(read_known_hosts(filename))

_ping_patterns = list(map(re.compile, [
	r'PING (\w+[.]?)+ \((\d+[.]?)+\) from (\d+[.]?)+ [a-z0-9]+: \d+\(\d+\) bytes of data.',
	r'PING (\w+[.]?)+ \((\d+[.]?)+\) \d+\(\d+\) bytes of data.',
	r'--- (\w+[.]?)+ ping statistics ---',
	r'ping: Warning: source address might be selected on device other than .*',
	]))

def _clear_ping_output(lines):
	for line in lines:
		if not line.strip():
			continue
		skip = False
		for pattern in _ping_patterns:
			if pattern.match(line):
				skip = True
				break
		if skip:
			continue
		yield line

def knock(host, interface=None, verbose=False): # pragma: no cover -- TODO calls command.
	""" Returns True if given host responded for ping.
	If interface is not None, uses that network interface to send packages.
	If verbose is True, prints some info about each ping to stderr.
	"""
	args = ["ping", "-q", "-c", "1", "-s", "1", "-W", "2"]
	if interface:
		args += ['-I', interface]
	args += [host]
	try:
		output = subprocess.check_output(args, stderr=subprocess.STDOUT)
		rc = 0
	except subprocess.CalledProcessError as e:
		output = e.stdout
		rc = e.returncode
	if verbose:
		for line in _clear_ping_output(output.decode('utf-8', 'replace').splitlines()):
			print(line, file=sys.stderr)
	return rc == 0

def check_hosts(hosts=None, interface=None, verbose=False): # pragma: no cover -- TODO needs mocks.
	""" Pings given hosts: first check any random entry, then checks all hosts one by one.
	Returns True as soon as any host responded. False if none responded.
	If hosts are not specified, uses global list of known hosts
	(default are Google DNS + custom list of hosts in $XDG_DATA_HOME/known_hosts.lst).
	Interface and verbose are passed to knock(). See there for details.
	"""
	hosts = hosts or known_hosts
	if len(hosts) > 1:
		host = random.choice(hosts)
		if knock(host, interface=interface, verbose=verbose):
			return True
	for host in hosts:
		if knock(host, interface=interface, verbose=verbose):
			return True
	return False

