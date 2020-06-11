import os
import getpass
import functools
try:
    from pathlib2 import Path
except ImportError: # pragma: no cover
    from pathlib import Path
import xdg.BaseDirectory

# Basic XDG structure.
XDG_CONFIG_HOME = Path(os.environ.get('XDG_CONFIG_HOME', Path('~').expanduser()/'.config'))
XDG_DATA_HOME = Path(os.environ.get('XDG_DATA_HOME', Path('~').expanduser()/'.local'/'share'))
XDG_CACHE_HOME = Path(os.environ.get('XDG_CACHE_HOME', Path('~').expanduser()/'.cache'))
XDG_RUNTIME_DIR = Path(os.environ.get('XDG_RUNTIME_DIR ', Path('/run')/'user'/getpass.getuser()))
# Non-standard setting for logs/history/app state etc.
# See https://stackoverflow.com/a/27965014/2128769
#     https://wiki.debian.org/XDGBaseDirectorySpecification#state
XDG_STATE_HOME = Path(os.environ.get('XDG_STATE_HOME', Path('~').expanduser()/'.state'))

# Ensuring physical XDG structure presence.
if not XDG_CONFIG_HOME.is_dir(): # pragma: no cover
    XDG_CONFIG_HOME.mkdir(parents=True, exist_ok=True)
if not XDG_CACHE_HOME.is_dir(): # pragma: no cover
    XDG_CACHE_HOME.mkdir(parents=True, exist_ok=True)
if not XDG_DATA_HOME.is_dir(): # pragma: no cover
    XDG_DATA_HOME.mkdir(parents=True, exist_ok=True)
if not XDG_STATE_HOME.is_dir(): # pragma: no cover
    XDG_STATE_HOME.mkdir(parents=True, exist_ok=True)

@functools.lru_cache()
def _save_XDG_path(xdg_dir, dirname):
    subdir = xdg_dir/dirname
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir

def save_config_path(dirname): return _save_XDG_path(XDG_CONFIG_HOME, dirname)
def save_data_path(dirname): return _save_XDG_path(XDG_DATA_HOME, dirname)
def save_cache_path(dirname): return _save_XDG_path(XDG_CACHE_HOME, dirname)
def save_state_path(dirname): return _save_XDG_path(XDG_STATE_HOME, dirname)
def save_runtime_path(dirname): return _save_XDG_path(XDG_RUNTIME_DIR, dirname)
