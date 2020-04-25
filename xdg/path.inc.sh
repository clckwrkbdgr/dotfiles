# Utility functions that allow to run executable from binpath other that the current one.

# Removes given dirname from the $PATH.
strip_from_path() { # <binpath directory>
	[ -z "$1" ] && return 1
	PATH="`echo "$PATH" | tr ':' '\n' | fgrep -v "${1}" | tr '\n' ':'`"
}

# Strips current script's directory from the $PATH.
strip_current_path() {
	strip_from_path "`dirname "$0"`"
}

# Main function.
# Should be called from a script put somewhere to $PATH.
# Script should be named exactly as the original (basic) executable.
# Example (e.g. for mocp it should be name exactly 'mocp'):
# #!/bin/sh
# . "$XDG_CONFIG_HOME/xdg/path.inc.sh" # -- optional, as it should be sourced from the main XDG script.
# exec_basic_executable <custom_args> "$@"
exec_basic_executable() { # <args...>
	strip_current_path
	export PATH
	executable_basename="`basename "$0"`"
	[ -n "$DEBUG_XDG" ] && which "$executable_basename"
	exec "$executable_basename" "$@"
}
