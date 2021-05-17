#!/bin/bash
# Unit-testing framework for Bash
# Basic usage:
# Each file is a separate test suite.
# Define test case functions:
#   test_something() {
#      do some actions here;
#      assertResults using number of built-in assertions;
#   }
# Functions setUp and tearDown are supported.
# Run unit tests:
#   unittest::run
# See specific functions for details.
#
# Test case functions are perfomed in subshell, so both exit or return are fine.
# All built-in assertions exit upon failure (with corresponding message to stderr).
# Messages use common format '<filename>:<line number>:<failed test case>:...
[ -n "$unittest_bash_is_already_sourced" ] && return
unittest_bash_is_already_sourced=1

. "$XDG_CONFIG_HOME/lib/utils.bash"

if ! which mktemp >/dev/null 2>&1; then
   mktemp() {
      # WARNING: have no security/concurrency safety like real mktemp does.
      while [ -n "$1" ]; do
         if [ "$1" == '--dry-run' ]; then
            dry_run=true
         elif [ "$1" == '--suffix' ]; then
            shift
            suffix="$1"
         elif [ "$1" == '-d' ]; then
            shift
            make_dir=true
         else
            panic "Unknown arguments to custom mktemp wrapper: $!"
         fi
         shift
      done

      tempdir="${TMPDIR:-${TEMP:-/tmp}}"
      tempfile="$tempdir/tmp$$-$(od -N4 -tu /dev/random | awk 'NR==1 {print $2} {}')${suffix}"
      if [ -z "$dry_run" ]; then
         if [ -n "$make_dir" ]; then
            mkdir "$tempfile"
         else
            touch "$tempfile"
         fi
      fi
      echo "$tempfile"
   }
fi

_QUIET_DIFF='diff'
if [ $(uname) == Linux ]; then
	_QUIET_DIFF='diff -q'
fi

files_equal() { # <left file> <right file>
	# Returns zero if files are equal, non-zero otherwise.
	# Does not produce any output.
	${_QUIET_DIFF} "$1" "$2" >/dev/null
}

if [ $(uname) == AIX ]; then
	_FIX_SPACES_IN_UNIFIED_DIFF=';s/^\([-+ ]\) /\1/'
	_FIX_METAINFO_IN_UNIFIED_DIFF=';s/^\(@@ -0\) /\1,0 /'
fi

unified_diff() { # <left file> <right file>
	# Produces just the difference in lines in unified diff format:
	# -removed line
	# +added line
	# Strips any header.
	left_file="$1"
	right_file="$2"
	left_file_name="${3:-$1}"
	right_file_name="${4:-$2}"
	diff -u "$left_file" "$right_file" | sed 's/^\([-+][-+][-+] .*\)\t[^\t]\+/\1/;1s|^\(--- \).*$|\1'"$left_file_name"'|;2s|^\(+++ \).*|\1'"$right_file_name"'|'"${_FIX_SPACES_IN_UNIFIED_DIFF}""${_FIX_METAINFO_IN_UNIFIED_DIFF}"
}

assertFilesSame() { # <actual> <expected>
	# Asserts that two files hold the same content.
	# Prints diff between files with the message.
	# Also fails if any of the files are missing.
	if [ ! -f "$1" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: First file does not exist: $1" >&2
		exit 1
	fi
	if [ ! -f "$2" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Second file does not exist: $2" >&2
		exit 1
	fi
	files_equal "$1" "$2" && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Files are not the same:' >&2
	unified_diff "$1" "$2" >&2
	exit 1
}

assertFilesDiffer() { # <actual> <expected>
	# Asserts that two files are not the same.
	# Prints content of the file(s) with the message.
	# Also fails if any of the files are missing.
	if [ ! -f "$1" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: First file does not exist: $1" >&2
		exit 1
	fi
	if [ ! -f "$2" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Second file does not exist: $2" >&2
		exit 1
	fi
	files_equal "$1" "$2" || return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Files do not differ:' >&2
	echo "--- $1" >&2
	echo "+++ $2" >&2
	cat "$1" >&2
	exit 1
}

assertStringsEqual() { # <actual> <expected>
	# Asserts that two given values are equal.
	[ "$1" == "$2" ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Strings are not equal:' >&2
	echo "Expected: '$1'" >&2
	echo "Actual: '$2'" >&2
	exit 1
}

assertStringsNotEqual() { # <actual> <expected>
	# Asserts that two given values are not equal.
	[ "$1" != "$2" ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Strings do not differ:' >&2
	echo "'$1'" >&2
	exit 1
}

assertStringEmpty() { # <value>
	# Asserts that given value is an empty string.
	[ -z "$1" ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'String is not empty:' >&2
	echo "'$1'" >&2
	exit 1
}

assertStringNotEmpty() { # <value>
	# Asserts that given value is not an empty string.
	[ -n "$1" ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'String is empty!' >&2
	exit 1
}

assertOutputEqual() { # <command> <expected_output>
	# Asserts that given command produces expected output.
	# If output param is specified as '-', read expected output from stdin:
	#   assertOutputEqual 'cat some_file' <<EOF
	#   ...well, you know.
	#   EOF
	# Otherwise expected output param may contain escape sequences (e.g. \n)
	# Command is executed in subshell, so `exit` is fine.
	# Return code is ignored, but stored in internals
	# so it can be checked later with assertReturnCode, assertExitSuccess, assertExitFailure without <command> arg (see description of corresponding function).
	# Prints the diff along with the message.
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
		exit 1
	fi
	local expected_output="$2"
	local actual_output_file=$(mktemp)
	local expected_output_file=$(mktemp)
	(
		if [ "$expected_output" == '-' ]; then
			cat >"$expected_output_file"
		else
			echo -e "$expected_output" >"$expected_output_file"
		fi
		( eval "$shell_command" >"$actual_output_file" )
	)
	_UNITTEST_LAST_RC=$?
	_UNITTEST_LAST_COMMAND="$shell_command"

	files_equal "$expected_output_file" "$actual_output_file"
	local diff_ok=$?
	if [ "$diff_ok" -eq 0 ]; then
		rm -f "$actual_output_file" "$expected_output_file"
		return 0
	fi
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command output differs:' >&2
	echo "$shell_command" >&2
	unified_diff "$expected_output_file" "$actual_output_file" "[expected]" "[actual]" >&2
	rm -f "$actual_output_file" "$expected_output_file"
	exit 1
}

assertOutputEmpty() { # <command>
	# Asserts that given command produces empty output (without even newlines).
	# See assertOutputEqual for other details.
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
		exit 1
	fi
	local actual_output_file=$(mktemp)
	local expected_empty_file=$(mktemp)
	(
		( eval "$shell_command" >"$actual_output_file" )
	)
	_UNITTEST_LAST_RC=$?
	_UNITTEST_LAST_COMMAND="$shell_command"

	files_equal "$expected_empty_file" "$actual_output_file"
	local diff_ok=$?
	if [ "$diff_ok" -eq 0 ]; then
		rm -f "$actual_output_file" "$expected_empty_file"
		return 0
	fi
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command output is not empty:' >&2
	echo "$shell_command" >&2
	unified_diff "$expected_empty_file" "$actual_output_file" "[expected: empty]" "[actual]" >&2
	rm -f "$actual_output_file" "$expected_empty_file"
	exit 1
}

assertReturnCode() { # <expected_rc> <command>
	# Asserts that command exits with expected return code.
	# RC should obviously be a number.
	# If command is omitted, result of previous assertOutputEqual is used, if there was one.
	# Command is executed in subshell, so `exit` is fine.
	local shell_command="$2"
	if [ -z "$shell_command" ]; then
		if [ -z "${_UNITTEST_LAST_RC}" ]; then
			echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
			exit 1
		fi
	fi
	local expected_rc="$1"
	if [ -z "$expected_rc" ]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Expected return code is empty!" >&2
		exit 1
	fi
	local number_re='^[0-9]+$'
	if ! [[ "$expected_rc" =~ $number_re ]]; then
		echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Expected return code is not a non-negative number!" >&2
		exit 1
	fi
	if [ -z "${_UNITTEST_LAST_RC}" ]; then
		( eval "$shell_command" )
		rc=$?
	else
		shell_command="${_UNITTEST_LAST_COMMAND}"
		rc="${_UNITTEST_LAST_RC}"
		_UNITTEST_LAST_COMMAND=
		_UNITTEST_LAST_RC=
	fi
	[ "$expected_rc" -eq "$rc" ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command return code differs:' >&2
	echo "$shell_command" >&2
	echo "Expected: $expected_rc" >&2
	echo "Actual: $rc" >&2
	exit 1
}

assertExitSuccess() { # <command>
	# Asserts that given command exits with RC=0
	# Otherwise follows assertReturnCode.
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		if [ -z "${_UNITTEST_LAST_RC}" ]; then
			echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
			exit 1
		fi
	fi
	if [ -z "${_UNITTEST_LAST_RC}" ]; then
		( eval "$shell_command" )
		rc=$?
	else
		shell_command="${_UNITTEST_LAST_COMMAND}"
		rc="${_UNITTEST_LAST_RC}"
		_UNITTEST_LAST_COMMAND=
		_UNITTEST_LAST_RC=
	fi
	[ "$rc" -eq 0 ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command did not exit with success:' >&2
	echo "$shell_command" >&2
	echo "Actual exit code: $rc" >&2
	exit 1
}

assertExitFailure() { # <command>
	# Asserts that given command exits with non-zero RC.
	# Otherwise follows assertReturnCode.
	local shell_command="$1"
	if [ -z "$shell_command" ]; then
		if [ -z "${_UNITTEST_LAST_RC}" ]; then
			echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Shell command is empty!" >&2
			exit 1
		fi
	fi
	if [ -z "${_UNITTEST_LAST_RC}" ]; then
		( eval "$shell_command" )
		rc=$?
	else
		shell_command="${_UNITTEST_LAST_COMMAND}"
		rc="${_UNITTEST_LAST_RC}"
		_UNITTEST_LAST_COMMAND=
		_UNITTEST_LAST_RC=
	fi
	[ "$rc" -ne 0 ] && return 0
	echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: Assert failed:" >&2
	echo 'Command did not exit with failure:' >&2
	echo "$shell_command" >&2
	echo "Actual exit code: $rc" >&2
	exit 1
}

unittest::run() {
	# Main unittest runner.
	# Usage: [<prefix>]
	#   <prefix>  - marks shell functions to execute as unit tests. Default is 'test_'
	# Runs all functions in local namespace that starts with specified prefix.
	# NOTE: Order of functions is undefined.
	# Prints statistics at the end: total cases, successes and failures.
	# Exit code is amount of failed test cases.
	# Set $UNITTEST_QUIET to omit final statistics.
	# NOTE: Is not executed in sourced files! Works only from the main script.
	local prefix="${1:-test_}"
	LAST_UNITTEST_PREFIX="$prefix"

	if [ -z "$FORCE_SOURCED_UNITTESTS" ]; then
		is_sourced "${BASH_SOURCE[1]}" && return 0
	fi

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
				finally tearDown
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

unittest::list() {
	# Prints all test cases defined in specified file to stdout.
	# Usage: unittest::list [<test_file.bash>]
	#   <test_file>  - Load specified test file instead of listing current scope.
	# NOTE: Order of functions is undefined.
	local filename="$1"
	(
		if [ -n "$filename" ]; then
			. "$filename" || panic "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: error while sourcing $filename"
		fi
		prefix="${LAST_UNITTEST_PREFIX}"
		if [ -z "$prefix" ]; then
			echo "${BASH_SOURCE[1]}:${BASH_LINENO[0]}:${FUNCNAME[1]}: cannot detect test case prefix in $filename, possibly unittest::run is not defined!" >&2
			exit 1
		fi

		for function_name in $(compgen -A function); do
			if [ "${function_name##$prefix}" == "${function_name}" ]; then
				continue
			fi
			echo "$function_name" 2>/dev/null # On AIX this line may protest against writting into dead pipe.
		done
	)
}

unittest::discover() {
	# Searchs for files with bash unit tests and executes them.
	# Usage: unittest::discover [<shell pattern>]
	#   <shell pattern>  - pattern to match test files (default is 'test_*.bash')
	# Return code is a sum of return codes of each found and executed test file.
	local pattern="${1:-test_*.bash}"
	find . -type f -name "$pattern" | (
		total_rc=0
		while read filename; do
			(
				bash "$filename"
			)
			rc=$?
			total_rc=$((total_rc + rc))
		done
		exit $total_rc
	)
	return ${PIPESTATUS[1]}
}

if ! is_sourced; then
	. "$XDG_CONFIG_HOME/lib/click.bash"
	click::command unittest_main 'Runs bash unit tests.'
	click::flag '-q' '--quiet' '' 'Produce less output, notify only about errors.'
	click::argument 'test_spec' "Unit test specification.
By default discovery is performed.
Test spec follows Python format:
  <dir>.<subdir>...<test_file>[.<test_case_spec>].
For bash unit tests modules match directories
and are separated with dots (.) instead of slashes (/).
Module part should match exact dir path.
Test case part is optional.
It may specify only beginning of the test case (e.g. test_, test_s etc),
or full test case name (test_something).
Any test case matching given prefix will be executed.
If test case is not specified, all test cases in the file are executed."
	# TODO [not-required-arguments] click::argument 'test_file_pattern' 'Pattern for test files (only for explicit "discover" action. By default test_*.bash are used.'
	unittest_main() {
		[ -n "${CLICK_ARGS[quiet]}" ] && export UNITTEST_QUIET=true

		if [ -z "${CLICK_ARGS[test_spec]}" -o "${CLICK_ARGS[test_spec]}" == 'discover' ]; then
			unittest::discover "${CLICK_ARGS[test_file_pattern]}"
			exit $?
		fi

		test_spec="${CLICK_ARGS[test_spec]}"
		find . -type f | (
			total_rc=0
			while read filename; do
				module_name="$(echo "$filename" | sed 's/^[.]\///;s/\//./g;s/[.]bash$//')"
				startswith "$test_spec" "$module_name" || continue
				(
					. "$filename"
					if [ "$module_name" == "$test_spec" ]; then
						unittest::run "${LAST_UNITTEST_PREFIX}"
					else
						unittest::list | while read test_case; do
							startswith "${module_name}.$test_case" "$test_spec" && exit 1
							continue
						done
						if [ $? == 1 ]; then
							test_case="${test_spec#${module_name}.}"
							unittest::run "$test_case"
						fi
					fi
				)
				rc=$?
				total_rc=$((total_rc + rc))
			done
			exit $total_rc
		)
		return ${PIPESTATUS[1]}
	}

	click::run "$@"
fi
