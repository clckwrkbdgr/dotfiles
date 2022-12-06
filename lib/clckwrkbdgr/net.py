from __future__ import print_function
import os, sys, subprocess
import platform
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

class Ping:
	DROP_PATTERNS = []

	def __init__(self, host, interface=None):
		self.host = host
		self.interface = interface
		self.rc = None
	def get_command(self): # pragma: no cover
		raise NotImplementedError

	def filter_output_lines(self, lines):
		for line in lines:
			if not line.strip():
				continue
			skip = False
			for pattern in self.DROP_PATTERNS:
				if pattern.match(line):
					skip = True
					break
			if skip:
				continue
			yield line
	def run(self): # pragma: no cover -- TODO
		try:
			args = self.get_command()
			self.output = subprocess.check_output(args, stderr=subprocess.STDOUT)
			self.rc = 0
		except subprocess.CalledProcessError as e:
			self.output = e.output
			self.rc = e.returncode
	def ok(self): # pragma: no cover -- TODO
		return self.rc == 0
	def iter_output(self):
		for line in self.filter_output_lines(self.output.decode('utf-8', 'replace').splitlines()):
			yield line

class WinPing(Ping): # pragma: no cover -- TODO
	DROP_PATTERNS = list(map(re.compile, [
		r'Pinging ([^. ]+[.]?)+ \[(\d+[.]?)+\] with \d+ bytes of data:',
		r'Ping statistics for (\d+[.]?)+:',
		r'    Packets: Sent = \d+, Received = \d+, Lost = \d+ \(\d+% loss\)',
		r'Approximate round trip times in milli-seconds:',
		r'    Minimum = \d+ms, Maximum = \d+ms, Average = \d+ms',
		]))
	def get_command(self):
		args = ["ping", "-n", "1", "-w", "2"]
		if self.interface:
			args += ['-S', self.interface]
		args += [self.host]
		return args

class UnixPing(Ping): # pragma: no cover -- TODO
	DROP_PATTERNS = list(map(re.compile, [
		r'PING ([^. ]+[.]?)+ \((\d+[.]?)+\) from (\d+[.]?)+ [a-z0-9]+: \d+\(\d+\) bytes of data.',
		r'PING ([^. ]+[.]?)+ \((\d+[.]?)+\) \d+\(\d+\) bytes of data.',
		r'--- ([^. ]+[.]?)+ ping statistics ---',
		r'ping: Warning: source address might be selected on device other than .*',
		]))
	TIMEOUT_OPTION = '-w'

	def get_command(self):
		args = ["ping", "-q", "-c", "1", "-s", "1", self.TIMEOUT_OPTION, "2"]
		if self.interface:
			args += ['-I', self.interface]
		args += [self.host]
		return args

class AIXPing(UnixPing): # pragma: no cover -- TODO
	pass

class LinuxPing(UnixPing): # pragma: no cover -- TODO
	TIMEOUT_OPTION = '-W'

def knock(host, interface=None, verbose=False): # pragma: no cover -- TODO calls command.
	""" Returns True if given host responded for ping.
	If interface is not None, uses that network interface to send packages.
	If verbose is True, prints some info about each ping to stderr.
	"""
	ping = {
			'Windows': WinPing,
			'AIX': AIXPing,
			'Linux': LinuxPing,
			}.get(platform.system(), UnixPing)(host, interface=interface)
	ping.run()
	if verbose:
		for line in ping.iter_output():
			print(line, file=sys.stderr)
	return ping.ok()

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

