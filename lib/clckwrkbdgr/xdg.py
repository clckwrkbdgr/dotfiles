from __future__ import absolute_import
import os
import getpass
import functools
import platform
from collections import namedtuple
try:
    from pathlib2 import Path
except ImportError: # pragma: no cover
    from pathlib import Path
import clckwrkbdgr._six

_XDGDir = namedtuple('_XDGDir', 'name path ensure')
# Basic XDG structure.
_dir_data = [
        _XDGDir('XDG_CONFIG_HOME', Path('~').expanduser()/'.config', True),
        _XDGDir('XDG_DATA_HOME', Path('~').expanduser()/'.local'/'share', True),
        _XDGDir('XDG_CACHE_HOME', Path('~').expanduser()/'.cache', True),
        ]
if platform.system() == 'Windows': # pragma: no cover -- Windows only.
    _dir_data += [
        _XDGDir('XDG_RUNTIME_DIR', Path(os.environ.get('TEMP', os.environ['USERPROFILE'])), False), # FIXME Proper default value.
        ]
else: # pragma: no cover -- Unix only.
    _dir_data += [
        _XDGDir('XDG_RUNTIME_DIR', Path('/run')/'user'/getpass.getuser(), False),
        ]
# Non-standard setting for logs/history/app state etc.
# See https://stackoverflow.com/a/27965014/2128769
#     https://wiki.debian.org/XDGBaseDirectorySpecification#state
_dir_data += [
        _XDGDir('XDG_STATE_HOME', Path('~').expanduser()/'.state', True),
        ]

for name, path, ensure in _dir_data: # pragma: no cover
    globals()[name] = Path(os.environ.get(name, path))
    if ensure:
        globals()[name].mkdir(parents=True, exist_ok=True)

@functools.lru_cache()
def _save_XDG_path(xdg_dir, *dirname):
    subdir = Path(xdg_dir).joinpath(*dirname)
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir

def save_config_path(*dirname): return _save_XDG_path(XDG_CONFIG_HOME, *dirname)
def save_data_path(*dirname): return _save_XDG_path(XDG_DATA_HOME, *dirname)
def save_cache_path(*dirname): return _save_XDG_path(XDG_CACHE_HOME, *dirname)
def save_state_path(*dirname): return _save_XDG_path(XDG_STATE_HOME, *dirname)
def save_runtime_path(*dirname): return _save_XDG_path(XDG_RUNTIME_DIR, *dirname)
