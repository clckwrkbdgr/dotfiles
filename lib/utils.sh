# TODO unittest.sh

panic() { # <message text>
	# Prints message to stderr and terminates the script.
	echo "$@" >&2
	exit 1
}

startswith() {
	# Usage:
	#   startswith "string" "prefix"
	# Returns 0 if <string> starts with <prefix>, non-zero otherwise.
	case "$1" in
		"$2"*) return 0;;
		*) return 1;;
	esac
}

trim() {
	# Removes heading and trailing whitespaces from the given values.
	# Prints result to stdout.
	local value="$*"
	value="${value#"${value%%[![:space:]]*}"}"
	value="${value%"${value##*[![:space:]]}"}"
	printf '%s' "$value"
}

item_in () {
	# Checks if given value is contained in given array.
	# Usage:
	#   item_in "value" "${array[@]}"
	# Origin: https://stackoverflow.com/a/8574392/2128769
	match="$1"
	shift
	for item; do [ "$item" == "$match" ] && return 0; done
	return 1
}

deprecated() {
	# Marks current scope (function, script, source file) as deprecated,
	# notifying about it to stderr.
	# Usage:
	#   deprecated 'Use X instead.'
	echo "$0:script/function is deprecated: $@" >&2
}

is_sourced() {
	# Bash-only.
	# Returns 0 if current file is being sourced from another file.
	# Returns non-zero if current file is the main script that is being executed.
	# If this function is called from another function,
	# which may be called for another sourced file,
	# you may want to explicitly specify current BASH_SOURCE.
	# Usage:
	#   is_source [<BASH_SOURCE>]
	if [ -n "$BASH" ]; then
		local bash_source="${1:-${BASH_SOURCE[1]}}"
		#echo "0 = $0"
		#echo "bash_source = $bash_source"
		if [ "$0" != "$bash_source" ]; then
			return 0
		fi
	else
		if [[ $_ != $0 ]]; then
			return 0
		fi
	fi
	return 1
}
