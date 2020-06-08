# Utility functions that allow to run executable from binpath other that the current one.
. "$XDG_CONFIG_HOME/lib/utils.bash"

# Removes given dirname from the $PATH.
strip_from_path() { # <binpath directory>
	deprecated 'Use path::strip from $XDG_CONFIG_HOME/lib/path.bash'
	. "$XDG_CONFIG_HOME/lib/path.bash"
	path::strip
}

# Strips current script's directory from the $PATH.
strip_current_path() {
	deprecated 'Use path::strip_current from $XDG_CONFIG_HOME/lib/path.bash'
	. "$XDG_CONFIG_HOME/lib/path.bash"
	path::strip_current
}

# Main function.
# Should be called from a script put somewhere to $PATH.
# Script should be named exactly as the original (basic) executable.
# Example (e.g. for mocp it should be name exactly 'mocp'):
# #!/bin/sh
# . "$XDG_CONFIG_HOME/xdg/path.inc.sh" # -- optional, as it should be sourced from the main XDG script.
# exec_basic_executable <custom_args> "$@"
exec_basic_executable() { # <args...>
	deprecated 'Use path::exec_base from $XDG_CONFIG_HOME/lib/path.bash'
	. "$XDG_CONFIG_HOME/lib/path.bash"
	path::exec_base "$@"
}
