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
