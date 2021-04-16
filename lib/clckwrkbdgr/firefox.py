try:
    import lz4.block
except ImportError: # pragma: no cover
    lz4 = None

def decompress_mozLz4(data): # pragma: no cover -- TODO needs mocks instead of just skipping.
    if not lz4:
        raise RuntimeError('Module lz4.block is not detected.')
    assert data[:8] == b'mozLz40\0'
    data = data[8:]
    return lz4.block.decompress(data)

def compress_mozLz4(data): # pragma: no cover -- TODO needs mocks instead of just skipping.
    if not lz4:
        raise RuntimeError('Module lz4.block is not detected.')
    return b'mozLz40\0' + lz4.block.compress(data)
