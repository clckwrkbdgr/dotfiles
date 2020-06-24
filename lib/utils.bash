panic() { # <message text>
	# Prints message to stderr and terminates the script.
	echo "$@" >&2
	exit 1
}

_finally_init () {
	# Defines shell actions to be performed upon exit
	# from the current scope (function, subshell).
	# Usage:
	#   finally 'do some cleanup;'
	#   finally 'do more cleanup;'
	# Note: this one is a helper function and should not be called directly.
	local next="$1"
	eval "finally () {
		local oldcmd='$(echo "$next" | sed -e s/\'/\'\\\\\'\'/g)'
		local newcmd=\"\$oldcmd; \$1\"
		trap -- \"\$newcmd\" 0
		_finally_init \"\$newcmd\"
	}"
}
_finally_init true

deprecated() {
	# Marks current scope (function, script, source file) as deprecated,
	# notifying about it to stderr.
	# Usage:
	#   deprecated 'Use X instead.'
	if [ "${FUNCNAME[1]}" == 'main' ]; then
		echo "$0:${BASH_LINENO[0]}:script is deprecated: $@" >&2
	elif [ "${FUNCNAME[1]}" == 'source' ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:script is deprecated: $@" >&2
	else
		echo "$0:${BASH_LINENO[0]}:function ${FUNCNAME[1]} is deprecated: $@" >&2
	fi
}

is_sourced() {
	# Bash-only.
	# Returns 0 if current file is being sourced from another file.
	# Returns non-zero if current file is the main script that is being executed.
	if [ -n "$BASH" ]; then
		if [ "$0" == "$BASH_SOURCE" ]; then
			return 0
		fi
	fi
	return 1
}
