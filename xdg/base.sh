# Basic XDG structure.
export XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$HOME/.config}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-$HOME/.cache}
export XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
# Non-standard setting for logs/history/app state etc.
# See https://stackoverflow.com/a/27965014/2128769
#     https://wiki.debian.org/XDGBaseDirectorySpecification#state
export XDG_STATE_HOME=${XDG_STATE_HOME:-$HOME/.state}
# Obsolete/deprecated settings.
export XDG_LOG_HOME=${XDG_STATE_HOME}

# Ensuring physical XDG structure presence.
[ -d "$XDG_CONFIG_HOME" ] || mkdir -p "$XDG_CONFIG_HOME"
[ -d "$XDG_CACHE_HOME"  ] || mkdir -p "$XDG_CACHE_HOME"
[ -d "$XDG_DATA_HOME"   ] || mkdir -p "$XDG_DATA_HOME"
[ -d "$XDG_STATE_HOME"  ] || mkdir -p "$XDG_STATE_HOME"

# Path to custom XDG wrappers for known cases.
export PATH="$XDG_CONFIG_HOME/xdg/bin:$PATH"
