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

# Searches for abs path to the real executable exluding the directory
# which contains current wrapper executable.
path::get_base_executable() {
	(
	path::strip_current
	which "`basename "$0"`"
	)
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
	executable_basename="$(path::get_base_executable)"
	[ -n "$DEBUG_XDG" ] && echo "$executable_basename" >&2
	exec "$executable_basename" "$@"
}

# Variation of exec_base, except $PATH is stripped and exported.
path::exec_base_strip_path() { # <args...>
	path::strip_current
	[ -n "$DEBUG_XDG" ] && echo "$PATH" >&2
	export PATH
	executable_basename="`basename "$0"`"
	[ -n "$DEBUG_XDG" ] && which "$executable_basename" >&2
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
	executable_basename="$(path::get_base_executable)"
	[ -n "$DEBUG_XDG" ] && echo "$executable_basename" >&2
	"$executable_basename" "$@"
}

# Variation of run_base, except $PATH is stripped and exported.
path::run_base_strip_path() { # <args...>
	path::strip_current
	[ -n "$DEBUG_XDG" ] && echo "$PATH" >&2
	export PATH
	executable_basename="`basename "$0"`"
	[ -n "$DEBUG_XDG" ] && which "$executable_basename" >&2
	"$executable_basename" "$@"
}
