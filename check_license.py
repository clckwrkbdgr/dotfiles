""" Searches for any specification of license in given path(s) (recursively).
If path is not given, current path is used.
Prints found resuls in in grep-like format '<filename>:<ln>:<found patterns>:<line>'
"""
import sys, os, re

def list_files(path):
	if os.path.isfile(path):
		yield path
		return
	for root, dirnames, filenames in os.walk(path):
		dirnames[:] = [dirname for dirname in dirnames if dirname != '.git']
		for filename in filenames:
			yield os.path.join(root, filename)

def grep(filename, patterns):
	with open(filename, 'rb') as f:
		for line_number, line in enumerate(f):
			line = line.decode('utf-8', 'replace')
			for pattern in patterns:
				matches = pattern.findall(line)
				if matches:
					line = line.rstrip()[:120]
					yield line_number, ','.join(map(str, matches)) + ':' + line

def search_in_files(path):
	patterns = [re.compile(pattern, flags=re.I) for pattern in [
		r'GPL',
		r'licen[sc]e',
		]]
	for filename in list_files(path):
		if filename == __file__:
			continue
		for line_number, text in grep(filename, patterns):
			yield '{0}:{1}:{2}'.format(filename, line_number, text)

if __name__ == '__main__':
	args = sys.argv[1:] or ['.']
	for arg in args:
		for result in search_in_files(arg):
			print(result)

