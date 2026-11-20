import sys, subprocess
from pathlib import Path
from clckwrkbdgr import xdg

def fix_last_track(): # pragma: no cover -- TODO
	""" Resumes last played item on the MOCP playlist (sort of).
	Last track ($XDG_CACHE_HOME/moc/last_track) is updated by mediasort.moc_submit_lastfm
	"""
	try:
		output = subprocess.check_output(['mocp', '-i'], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		output = e.stdout
	if b'FATAL_ERROR: The server is not running!' not in output:
		raise RuntimeError('Cannot fix last track when MOCP is running!')

	last_track = xdg.save_cache_path('moc')/'last_track'
	if not last_track.exists():
		return

	playlist = xdg.save_cache_path('moc')/'playlist.m3u'
	if not playlist.exists():
		return

	last_track, number = last_track.read_text().splitlines()
	number = int(number)

	lines = playlist.read_text().splitlines()
	# Because MOCP does not allow selecting a specific item on the playlist,
	# we will just remove all of the items before it.
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
				raise RuntimeError('Expected track {0} at {1} in {2}, found: {3}'.format(
					last_track, number, playlist, line,
					))
			continue
		if line.startswith('#EXTINF:'):
			if current == number:
				found_extinf = True
			current += 1
	playlist.write_text('\n'.join(fixed) + '\n')

import click

@click.group()
def cli(): # pragma: no cover
	pass

@cli.command('fix-last-track')
def command_fix_last_track(): # pragma: no cover
	fix_last_track()

if __name__ == '__main__': # pragma: no cover
	cli()
