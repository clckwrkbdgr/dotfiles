import lz4.block

def decompress_mozLz4(data):
    assert data[:8] == b'mozLz40\0'
    data = data[8:]
    return lz4.block.decompress(data)

def compress_mozLz4(data):
    return b'mozLz40\0' + lz4.block.compress(data)
