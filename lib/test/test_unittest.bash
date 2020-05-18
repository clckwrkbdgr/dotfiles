#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

(
	test_test() {
		echo 'executed'
	}
	output=$(unittest::run)
	[ "$output" == 'executed' ]
) || panic 'Test is not executed!'

(
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'first'
	}
	TMPFILE=$(mktemp)
	echo -e "first\nsecond" >"$TMPFILE"
	trap "rm $TMPFILE" EXIT
	unittest::run | diff - "$TMPFILE"
) || panic 'Tests are not executed in order of definition!'

(
	custom_test_test() {
		echo 'executed'
	}
	output=$(unittest::run custom_test)
	[ "$output" == 'executed' ]
) || panic 'Custom test prefix is not recognized!'

(
	setup() {
		echo 'setup'
	}
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	TMPFILE=$(mktemp)
	echo -e "setup\nfirst\nsetup\nsecond" >"$TMPFILE"
	trap "rm $TMPFILE" EXIT
	unittest::run | diff - "$TMPFILE"
) || panic 'Setup action is not executed for each test!'

(
	teardown() {
		echo 'teardown'
	}
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	TMPFILE=$(mktemp)
	echo -e "first\nteardown\nsecond\nteardown" >"$TMPFILE"
	trap "rm $TMPFILE" EXIT
	unittest::run | diff - "$TMPFILE"
) || panic 'Teardown action is not executed for each test!'

(
	setup() {
		echo 'setup'
	}
	teardown() {
		echo 'teardown'
	}
	test_first() {
		exit 1
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	TMPFILE=$(mktemp)
	echo -e "setup\nteardown\nsetup\nsecond\nteardown" >"$TMPFILE"
	trap "rm $TMPFILE" EXIT
	( unittest::run ) | diff - "$TMPFILE"
) || panic 'Teardown action is not executed in case of fatal error!'

(
	[ -z "$UNITTEST_EXPORTED_VALUE" ] || panic '$UNITTEST_EXPORTED_VALUE is present in env, cannot reuse for testing purposes!'
	test_first() {
		export UNITTEST_EXPORTED_VALUE=1
	}
	unittest::run
	[ -z "$UNITTEST_EXPORTED_VALUE" ]
) || panic 'Environment from the test is not isolated and available after!'

(
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	TMPFILE=$(mktemp)
	echo -e "first\nsecond" >"$TMPFILE"
	trap "rm $TMPFILE" EXIT

	TMPSTATFILE=$(mktemp)
	echo -e "Executed: 2 test(s).\nSuccessful: 2 test(s).\nOK" >"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run | diff - "$TMPFILE" 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Stats are not printed correctly!'

(
	test_first() {
		echo 'first'
	}
	test_second() {
		exit 1
	}
	TMPFILE=$(mktemp)
	echo -e "first\nsecond" >"$TMPFILE"
	trap "rm $TMPFILE" EXIT

	TMPSTATFILE=$(mktemp)
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run | diff - "$TMPFILE" 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Failures are not displayed in stats!'

(
	FIRST_TMPFILE=$(mktemp)
	SECOND_TMPFILE=$(mktemp)
	test_same() {
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "a\nb" >"$SECOND_TMPFILE"
		assertFilesSame "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}
	test_differ() {
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "c\nb" >"$SECOND_TMPFILE"
		assertFilesSame "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differ: Assert failed:\nFiles are not the same:\ndiff $FIRST_TMPFILE $SECOND_TMPFILE\n---\na\n+++\nc" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Files are not checked to be the same!'

(
	FIRST_TMPFILE=$(mktemp)
	SECOND_TMPFILE=$(mktemp)
	test_same() {
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "a\nb" >"$SECOND_TMPFILE"
		assertFilesDiffer "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}
	test_differ() {
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "c\nb" >"$SECOND_TMPFILE"
		assertFilesDiffer "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_same: Assert failed:\nFiles do not differ:\ndiff $FIRST_TMPFILE $SECOND_TMPFILE\na\nb" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Files are not checked to be different!'

(
	test_same() {
		FIRST='first'
		SECOND='first'
		assertStringsSame "$FIRST" "$SECOND"
	}
	test_differ() {
		FIRST='first'
		SECOND='second'
		assertStringsSame "$FIRST" "$SECOND"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differ: Assert failed:\nStrings are not same:\nExpected: first\nActual: second" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Strings are not checked to be same!'

(
	test_same() {
		FIRST='first'
		SECOND='first'
		assertStringsSame "$FIRST" "$SECOND"
	}
	test_differ() {
		FIRST='first'
		SECOND='second'
		assertStringsSame "$FIRST" "$SECOND"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_same: Assert failed:\nStrings do not differ:\nfirst" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Strings are not checked to be different!'

(
	test_empty() {
		assertStringEmpty ""
	}
	test_not_empty() {
		assertStringEmpty "content"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_not_empty: Assert failed:\nString is not empty:\ncontent" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Strings are not checked to be empty!'

(
	test_empty() {
		assertStringNotEmpty ""
	}
	test_not_empty() {
		assertStringNotEmpty "content"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_empty: Assert failed:\nString is empty!" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Strings are not checked to be not empty!'

(
	test_same() {
		assertOutputSame 'echo -e "first\nsecond"' "first\nsecond"
	}
	test_differs() {
		assertOutputSame 'echo -e "first\nsecond"' "differs"
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differs: Assert failed:\nCommand output differs:\necho -e \"first\\nsecond\"\n---\nfirst\nsecond\n+++\ndiffers" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Command output is not checked against expected value!'

(
	test_same() {
		echo "first\nsecond" | assertOutputSame 'echo -e "first\nsecond"' -
	}
	test_dash_on_stdin() {
		echo -- - | assertOutputSame 'echo -- -' -
	}
	test_differs() {
		echo "differs" | assertOutputSame 'echo -e "first\nsecond"' -
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differs: Assert failed:\nCommand output differs:\necho -e \"first\\nsecond\"\n---\nfirst\nsecond\n+++\ndiffers" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Command output is not checked against expected stdin!'

(
	test_same() {
		assertReturnCode 'exit 1' 1
	}
	test_differs() {
		assertReturnCode 'exit 0' 1
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differs: Assert failed:\nCommand return code differs:\nexit 0\nExpected: 1\nActual: 0" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Command return code is not checked!'

(
	test_success() {
		assertExitSuccess 'exit 0'
	}
	test_failure() {
		assertExitSuccess 'exit 1'
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differs: Assert failed:\nCommand did not exit with success:\nexit 1\nActual exit code: 1" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Command success is not checked!'

(
	test_success() {
		assertExitFailure 'exit 0'
	}
	test_failure() {
		assertExitFailure 'exit 1'
	}

	TMPSTATFILE=$(mktemp)
	echo -e "test_differs: Assert failed:\nCommand did not exit with failure:\nexit 0\nActual exit code: 0" >>"$TMPSTATFILE"
	echo -e "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 tests(s).\nFAIL" >>"$TMPSTATFILE"
	trap "rm $TMPSTATFILE" EXIT
	( unittest::run 2>&1 ) 3>&2 2>&1 1>&3  | diff - "$TMPSTATFILE"
) || panic 'Command failure is not checked!'
