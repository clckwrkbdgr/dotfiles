#!/usr/bin/env python
import os, sys, io
import click
from clckwrkbdgr import firefox

bin_stdin = io.open(sys.stdin.fileno(), 'rb')
bin_stdout = io.open(sys.stdout.fileno(), 'wb')

@click.group()
def cli():
    """ Filter to compress/decompress mozLz4 streams. """
    pass

@cli.command()
def compress():
    """ Compresses stdin data stream to mozLz4 stdout. """
    bin_stdout.write(firefox.compress_mozLz4(bin_stdin.read()))

@cli.command()
def decompress():
    """ Decompresses stdin mozLz4 stream to stdout. """
    bin_stdout.write(firefox.decompress_mozLz4(bin_stdin.read()))

if __name__ == '__main__':
    cli()
