#!/usr/bin/env python
import sys, subprocess
from pathlib import Path
from clckwrkbdgr import xdg
import clckwrkbdgr.jobsequence.context
context = clckwrkbdgr.jobsequence.context.init(
    working_dir=xdg.XDG_CONFIG_HOME,
    )

# autostart mocp on last lastfm entry

from clckwrkbdgr.pyshell import which
if not which('mocp'):
	context.done()

try:
	mocp = subprocess.check_output(['mocp', '-i'], stderr=subprocess.STDOUT).decode('utf-8', 'replace').splitlines()
	if any(line.startswith('File: ') for line in mocp):
		context.info('MOC is already playing, will not force resume.')
	else:
		context.warning('MOC is started but not playing, will not force resume.')
	context.done()
except subprocess.CalledProcessError as e:
	if b'FATAL_ERROR: The server is not running!' in e.stdout:
		pass # Expected
	else:
		context.warning('MOC info responded with error: stdout={0}, stderr={1}'.format(e.stdout, e.stderr))
		context.done()

last_track = xdg.save_cache_path('moc')/'last_track'
if not last_track.exists():
	context.done()

playlist = xdg.save_cache_path('moc')/'playlist.m3u'
if not playlist.exists():
	context.done()

last_track, number = last_track.read_text().splitlines()
number = int(number)

lines = playlist.read_text().splitlines()
fixed = []
found_extinf = False
verified_path = False
current = 0
for line in lines:
	if line.startswith('#') and not line.startswith('#EXTINF:'):
		fixed.append(line)
		continue
	if found_extinf:
		if verified_path:
			fixed.append(line)
			continue
		verified_path = line == last_track
		if not verified_path:
			context.error('Expected track {0} at {1} in {2}, found: {3}'.format(
				last_track, number, playlist, line,
				))
			sys.exit(1)
		continue
	if line.startswith('#EXTINF:'):
		if current == number:
			found_extinf = True
			print(line)
		current += 1
playlist.write_text('\n'.join(fixed) + '\n')
