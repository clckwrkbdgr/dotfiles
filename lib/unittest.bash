assertFilesSame() { # <actual> <expected>
	if [ ! -f "$1" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: First file does not exist: $1" >&2
		exit 1
	fi
	if [ ! -f "$2" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Second file does not exist: $2" >&2
		exit 1
	fi
	diff -q "$1" "$2" >/dev/null && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Files are not the same:' >&2
	diff -u "$1" "$2" | sed 's/^\([-+][-+][-+] .*\)\t[^\t]\+/\1/' >&2
	exit 1
}

assertFilesDiffer() { # <actual> <expected>
	if [ ! -f "$1" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: First file does not exist: $1" >&2
		exit 1
	fi
	if [ ! -f "$2" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Second file does not exist: $2" >&2
		exit 1
	fi
	diff -q "$1" "$2" >/dev/null || return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Files do not differ:' >&2
	echo "--- $1" >&2
	echo "+++ $2" >&2
	cat "$1" >&2
	exit 1
}

assertStringsEqual() { # <actual> <expected>
	[ "$1" == "$2" ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Strings are not equal:' >&2
	echo "Expected: '$1'" >&2
	echo "Actual: '$2'" >&2
	exit 1
}

assertStringsNotEqual() { # <actual> <expected>
	[ "$1" != "$2" ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Strings do not differ:' >&2
	echo "'$1'" >&2
	exit 1
}

assertStringEmpty() { # <value>
	[ -z "$1" ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'String is not empty:' >&2
	echo "'$1'" >&2
	exit 1
}

assertStringNotEmpty() { # <value>
	[ -n "$1" ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'String is empty!' >&2
	exit 1
}

assertOutputEqual() { # <command> <expected_output>
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
		exit 1
	fi
	local expected_output="$2"
	local actual_output_file=$(mktemp)
	local expected_output_file=$(mktemp)
	trap "rm -f '$actual_output_file' '$expected_output_file'" EXIT
	if [ "$expected_output" == '-' ]; then
		cat >"$expected_output_file"
	else
		echo -e "$expected_output" >"$expected_output_file"
	fi
	( eval "$shell_command" >"$actual_output_file" )

	diff -q "$expected_output_file" "$actual_output_file" >/dev/null && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command output differs:' >&2
	echo "$shell_command" >&2
	diff -u "$expected_output_file" "$actual_output_file" | sed 's/^\([-+][-+][-+] .*\)\t[^\t]\+/\1/;1s/^\(--- \).*$/\1[expected]/;2s/^\(+++ \).*/\1[actual]/' >&2
	exit 1
}

assertReturnCode() { # <expected_rc> <command>
	local shell_command="$2"
	if [ -z "$shell_command" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
		exit 1
	fi
	local expected_rc="$1"
	if [ -z "$expected_rc" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Expected return code is empty!" >&2
		exit 1
	fi
	local number_re='^[0-9]+$'
	if ! [[ "$expected_rc" =~ $number_re ]]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Expected return code is not a number!" >&2
		exit 1
	fi
	( eval "$shell_command" )
	rc=$?
	[ "$expected_rc" -eq "$rc" ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command return code differs:' >&2
	echo "$shell_command" >&2
	echo "Expected: $expected_rc" >&2
	echo "Actual: $rc" >&2
	exit 1
}

assertExitSuccess() { # <command>
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
		exit 1
	fi
	( eval "$shell_command" )
	rc=$?
	[ "$rc" -eq 0 ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command did not exit with success:' >&2
	echo "$shell_command" >&2
	echo "Actual exit code: $rc" >&2
	exit 1
}

assertExitFailure() { # <command>
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
		exit 1
	fi
	( eval "$shell_command" )
	rc=$?
	[ "$rc" -ne 0 ] && return 0
	echo "$0:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command did not exit with failure:' >&2
	echo "$shell_command" >&2
	echo "Actual exit code: $rc" >&2
	exit 1
}

unittest::run() {
	# Usage: [<prefix>]
	#   <prefix>  - marks shell functions to execute as unit tests. Default is 'test_'
	# Set $UNITTEST_QUIET to omit final statistics.

	local prefix="${1:-test_}"
	# TODO use click
	local quiet="$UNITTEST_QUIET"

	local has_setUp=$(compgen -A function | grep '^setUp$')
	local has_tearDown=$(compgen -A function | grep '^tearDown$')
	
	local total=0
	local successful=0
	local failed=0
	for function_name in $(compgen -A function); do
		if [ "${function_name##$prefix}" == "${function_name}" ]; then
			continue
		fi
		total=$((total + 1))

		(
			if [ -n "$has_setUp" ]; then
				setUp
			fi
			if [ -n "$has_tearDown" ]; then
				trap tearDown EXIT
			fi
			"$function_name"
		)
		rc=$?
		if [ "$rc" == 0 ]; then
			successful=$((successful + 1))
		else
			#TODO shopt -s extdebug to print location
			failed=$((failed + 1))
		fi
	done
	if [ -z "$quiet" ]; then
		echo "Executed: $total test(s)." >&2
		if [ "$successful" -gt 0 ]; then
			echo "Successful: $successful test(s)." >&2
		fi
		if [ "$failed" -gt 0 ]; then
			echo "Failures: $failed test(s)." >&2
		fi
		if [ "$failed" -gt 0 ]; then
			echo 'FAIL' >&2
		else
			echo 'OK' >&2
		fi
	fi
	if [ "$failed" -gt 0 ]; then
		return $failed
	fi
	return 0
}
