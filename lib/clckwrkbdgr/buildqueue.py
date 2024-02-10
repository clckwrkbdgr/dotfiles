""" Build workers (Continuous Integration)
"""
import subprocess, shlex
import re
from . import utils

AT_JOB_ID = re.compile(b'job (\\d+) at \\w+ \\w+ +\\d+ \\d+:\\d+:\\d+ \\d+$')

def run_command(command, start_dir=None, env=None): # pragma: no cover -- TODO
	""" Runs shell command via build queue.
	If command is a list, uses shlex to construct a shell command from arguments.
	If start_dir is specifies, sets it as a current directory before executing command.
	If env is specified, it should be a dict or a list of pairs: (env_varirable_name, value)
	Returns job id.
	Raises RuntimeError if failed to register command.
	"""
	# TODO detect other means of running scheduled commands in a queue and pick automatically.
	if utils.is_collection(command):
		command = ' '.join(map(shlex.quote, command))
	if env:
		for name, value in dict(env).items():
			command = 'export {0}={1}; '.format(str(name), shlex.quote(str(value))) + command
	if start_dir:
		command = 'cd {0}; '.format(shlex.quote(str(start_dir))) + command
	at = subprocess.Popen(['at', 'now'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = at.communicate(command.encode('utf-8', 'replace'))
	filtered_stderr = []
	job_id = None
	for line in stderr.splitlines():
		m = AT_JOB_ID.match(line)
		if m:
			job_id = int(m.group(1))
			continue
		if line == b'warning: commands will be executed using /bin/sh':
			continue
		filtered_stderr.append(line)
	stderr = b'\n'.join(filtered_stderr)
	rc = at.wait()
	if rc != 0 or not job_id:
		raise RuntimeError('Failed to register "at" command:' + '\n'.join(filter(None, (
			'RC={0}'.format(rc),
			'job_id={0}'.format(job_id),
			'stdout: {0}'.format(stdout) if stdout else None,
			'stderr: {0}'.format(stderr) if stderr else None,
			))))
	return job_id
