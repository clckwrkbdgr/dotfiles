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

endswith() {
	# Usage:
	#   endswith "string" "suffix"
	# Returns 0 if <string> ends with <suffix>, non-zero otherwise.
	case "$1" in
		*"$2") return 0;;
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
	local item match="$1"
	shift
	for item; do [[ "$item" == "$match" ]] && return 0; done
	return 1
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
	# If this function is called from another function,
	# which may be called for another sourced file,
	# you may want to explicitly specify current BASH_SOURCE.
	# Usage:
	#   is_source [<BASH_SOURCE>]
	local bash_source="${1:-${BASH_SOURCE[1]}}"
	if [ -n "$BASH" ]; then
		#echo "0 = $0"
		#echo "bash_source = $bash_source"
		if [ "$0" != "$bash_source" ]; then
			return 0
		fi
	fi
	return 1
}

as_uri() {
	# Converts local file path to URI: file://...
	# File must exist.
	local pathlib_import="pathlib"
	if [ 2 == $(python -c 'import sys;print(sys.version_info[0])') ]; then
		pathlib_import="pathlib2 as pathlib"
	fi
	python -c "import sys,${pathlib_import}; print(pathlib.Path(sys.argv[1]).resolve().as_uri())" "$1"
}

truncate_logfile() {
	# Shrinks given file to the last N lines.
	# Usage:
	#   truncate_logfile my.log 50
	[ -z "${1}${2}" ] && return 1
	local _total_lines=$(wc -l <"$1")
	[ "${_total_lines}" -le "${2}" ] && return 0
	if sed --version 2>&1 | grep -q GNU; then
		sed -i "1,$((_total_lines-${2:-0}))d" "$1"
	else
		local tempfile="$(mktemp)"
		finally "rm -f '$tempfile'"
		tail -n "${2}" "$1" >"$tempfile" && mv -f "$tempfile" "$1"
	fi
}

version_cmp() {
	# Compares two dot-separated version strings (respecting sections).
	# Returns (prints to stdout):
	#   '<', if L < R,
	#   '>', if L > R,
	#   '=', if L == R
	# Usage:
	#   version_cmp <version L> <version R>
	if [ -z "$1" -a -z "$2" ]; then
		echo '='
		return
	fi
	if [ -z "$1" ]; then
		echo '<'
		return
	fi
	if [ -z "$2" ]; then
		echo '>'
		return
	fi
	head1=${1%%.*}
	head2=${2%%.*}
	if (( $head1 < $head2 )); then
		echo '<'
		return
	elif (( $head1 > $head2 )); then
		echo '>'
		return
	fi
	tail1=${1#*.}
	[ "$tail1" == "$1" ] && tail1='' # Detecting last section (no dots left).
	tail2=${2#*.}
	[ "$tail2" == "$2" ] && tail2='' # Detecting last section (no dots left).
	version_cmp "$tail1" "$tail2"
}
