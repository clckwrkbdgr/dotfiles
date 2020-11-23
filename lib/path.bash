# Utility functions that allow to run executable from binpath other that the current one.

# Removes given dirname from the $PATH (or specified variable).
path::strip() { # <binpath directory> [<path variable name, default is PATH>]
	[ -z "$1" ] && return 1
	varname="${2:-PATH}"
	eval "value=\"\$${varname}\""
	value="`echo "$value" | tr ':' '\n' | fgrep -v "${1}" | tr '\n' ':' | sed 's/:*$//'`"
	eval "${varname}='$value'"
}

# Strips current script's directory from the $PATH.
path::strip_current() {
	path::strip "`dirname "$0"`"
}

# Main function.
# This version replaces current process (using shell builtin `exec`)
# Should be called from a script put somewhere to $PATH.
# Script should be named exactly as the original (basic) executable.
# Example (e.g. for mocp it should be name exactly 'mocp'):
# #!/bin/sh
# . "$XDG_CONFIG_HOME/lib/path.bash"
# path::exec_base <custom_args> "$@"
path::exec_base() { # <args...>
	path::strip_current
	[ -n "$DEBUG_XDG" ] && echo "$PATH"
	export PATH
	executable_basename="`basename "$0"`"
	[ -n "$DEBUG_XDG" ] && which "$executable_basename"
	exec "$executable_basename" "$@"
}

# Main function.
# This version executes command, waits for it to finish and return RC.
# Should be called from a script put somewhere to $PATH.
# Script should be named exactly as the original (basic) executable.
# Example (e.g. for mocp it should be name exactly 'mocp'):
# #!/bin/sh
# . "$XDG_CONFIG_HOME/lib/path.bash"
# path::run_base <custom_args> "$@"
path::run_base() { # <args...>
	path::strip_current
	[ -n "$DEBUG_XDG" ] && echo "$PATH"
	export PATH
	executable_basename="`basename "$0"`"
	[ -n "$DEBUG_XDG" ] && which "$executable_basename"
	"$executable_basename" "$@"
}
