import os, sys, subprocess
try:
	subprocess.DEVNULL
except AttributeError: # pragma: no cover
	subprocess.DEVNULL = open(os.devnull, 'w')
import datetime
import traceback
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path

def run(args):
	""" Runs command and return its exit code. """
	return subprocess.call(args)

def run_quiet(args):
	""" Runs command quietly (no output) and just returns its exit code. """
	return subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_detached(args):
	""" Runs command in background, ignore all output and return immediately. """
	return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_terminal(args):
	""" Runs command in external standalone terminal instance. """
	return run_detached(['urxvt', '-e'] + args) # TODO other types of terminals

def get_output(args, encoding='utf-8'):
	""" Runs command and return its decoded output.
	Ignores failure exit codes.
	"""
	try:
		return subprocess.check_output(args).decode(encoding, 'replace')
	except subprocess.CalledProcessError as e:
		return e.output.decode(encoding, 'replace')

def pipe(args, input_text, encoding='utf-8'):
	""" Runs command, feeds given input and return its decoded output.
	Ignores failure exit codes.
	"""
	p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	stdout, _ = p.communicate(input_text.encode(encoding, 'replace'))
	p.wait()
	return stdout.decode(encoding, 'replace')

def run_command_and_collect_output(args, start_dir=None, output_dir=None): # pragma: no cover -- TODO accesses and uses FS, subprocesses
	""" Imitates Unix crontab job.

	Runs batch command with arguments and collects output.
	Completely disables STDIN for the process (redirects DEVNULL)
	to prevent subprocesses being locked on waiting input.

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

	old_cwd = os.getcwd()
	try:
		if start_dir:
			try:
				os.chdir(str(start_dir))
			except:
				pass
		pid = hash(str(args))
		try:
			p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, shell=True)
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
	finally:
		try:
			os.chdir(old_cwd)
		except:
			pass

def has_sudo_rights(): # pragma: no cover -- TODO executes command and parses output.
	try:
		output = subprocess.check_output(['/usr/bin/sudo', '--list', '--non-interactive'], stderr=subprocess.STDOUT)
		output = output.replace(b' ', b'')
		return b'ALL:ALL' in output
	except subprocess.CalledProcessError:
		return False

import click

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, required=True)
@click.option('--start-dir', help='Start directory. Default is current.')
@click.option('--output-dir', help='Directory to store job log file if there was any. By default is $HOME (%USERPROFILE%).')
def cli(args, start_dir=None, output_dir=None): # pragma: no cover
	""" Runs program and collects its output/stderr.
	
	Creates trace file if there was any output or if program exited with non-zero.
	"""
	run_command_and_collect_output(args, start_dir=start_dir, output_dir=output_dir)

if __name__ == '__main__': # pragma: no cover
	cli()
