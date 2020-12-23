import os, sys, subprocess
import datetime
import traceback
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

def run_command_and_collect_output(args, output_dir=None): # pragma: no cover -- TODO accesses and uses FS, subprocesses
	""" Imitates Unix crontab job.

	Runs command with arguments and collects output.

	If command returned non-zero and generated any output on stdout or stderr,
	collects output with some additional info (similar to crontab MAILTO feature),
	and then stores collected data into logfile in specified directory.
	Default output directory is $HOME (%USERPROFILE% on Windows).

	Returns exit code from command.
	"""
	args = list(args)
	now = datetime.datetime.now()
	formatted_now = now.strftime('%Y-%m-%d-%H-%M-%S')
	output_dir = Path(output_dir or os.environ.get('USERPROFILE', os.environ['HOME']))

	try:
		pid = hash(str(args))
		try:
			p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
			pid = p.pid
			command_output, _ = p.communicate()
			assert(_ is None)
			returncode = p.wait()
		except:
			command_output = traceback.format_exc().encode('utf-8', 'replace')
			returncode = -1

		if returncode != 0 or command_output:
			filename = '{0}-{1}-crontab.log'.format(formatted_now, pid)
			with (output_dir/filename).open('wb') as f:
				f.write("Start: {0}\n".format(now).encode('utf-8', 'replace'))
				f.write("Args: {0}\n".format(args).encode('utf-8', 'replace'))
				f.write(b"\n")
				f.write("Return code: {0}\n".format(returncode).encode('utf-8', 'replace'))
				f.write(b"\n")
				f.write(command_output)
		return returncode
	except:
		with (output_dir/'{0}-crontab-error.log'.format(formatted_now)).open('wb') as f:
			f.write(traceback.format_exc().encode('utf-8', 'replace'))
		return -1

import click

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, required=True)
@click.option('--output-dir', help='Directory to store job log file if there was any. By default is $HOME (%USERPROFILE%).')
def cli(args, output_dir): # pragma: no cover
	""" Runs program and collects its output/stderr.
	
	Creates trace file if there was any output or if program exited with non-zero.
	"""
	run_command_and_collect_output(args, output_dir)

if __name__ == '__main__': # pragma: no cover
	cli()
