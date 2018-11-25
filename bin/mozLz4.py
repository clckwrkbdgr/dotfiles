#!/usr/bin/python3
import os, sys, io
import lz4.block

def decompress(data):
    assert data[:8] == b'mozLz40\0'
    data = data[8:]
    return lz4.block.decompress(data)

def compress(data):
    return b'mozLz40\0' + lz4.block.compress(data)

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        raise Exception('Command is not specified! Should be either `compress` or `decompress`')
    bin_stdin = io.open(sys.stdin.fileno(), 'rb')
    bin_stdout = io.open(sys.stdout.fileno(), 'wb')
    if args[0] == 'compress':
        bin_stdout.write(compress(bin_stdin.read()))
    elif args[0] == 'decompress':
        bin_stdout.write(decompress(bin_stdin.read()))
    else:
        raise Exception('Unknown command `{0}`! Should be either `compress` or `decompress`'.format(args[0]))
