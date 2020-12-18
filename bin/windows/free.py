import datetime
import subprocess
import click

@click.command()
@click.option('-l', 'single_line', is_flag=True, help='Print all values in one line, like Unix `free`')
@click.option('-t', 'print_time', is_flag=True, help='Print current time.')
@click.option('-H', 'print_header', is_flag=True, help='Print header.')
def cli(single_line=False, print_time=False, print_header=False):
	output = subprocess.check_output(['wmic', 'OS', 'get', 'FreePhysicalMemory,FreeVirtualMemory,TotalVirtualMemorySize,TotalVisibleMemorySize'])
	output = output.decode('utf-8', 'replace')
	memory = dict(zip(*map(str.split, filter(lambda x:x.strip(), output.splitlines()))))
	name_column = max(map(len, memory.keys()))
	value_column = max(map(len, memory.values()))

	if single_line:
		timestamp = ''
		if print_time:
			timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S  ')
		column = max(name_column, value_column)
		names, values = zip(*(memory.items()))
		if print_header:
			fmt = '{0: >%d}' % (column,)
			print(timestamp + '  '.join(fmt.format(name) for name in names))
		fmt = '{0: >%d,}' % (column,)
		print(timestamp + '  '.join(fmt.format(int(value)).replace(',', ' ') for value in values))
	else:
		fmt = '{0:%d} {1: >%d,}' % (name_column + 2, value_column * 1.3)
		for name, value in memory.items():
			print(fmt.format(name, int(value)).replace(',', ' '))

if __name__ == '__main__':
	cli()
