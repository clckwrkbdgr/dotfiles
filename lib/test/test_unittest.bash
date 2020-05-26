#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

selftest_execute_single_test() {
	test_test() {
		echo 'executed'
	}
	UNITTEST_QUIET=true
	output=$(unittest::run)
	assertStringsEqual "$output" 'executed'
}

selftest_execute_multiple_tests() {
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	UNITTEST_QUIET=true
	assertOutputEqual unittest::run "first\nsecond"
}

selftest_custom_test_prefix() {
	custom_test_test() {
		echo 'executed'
	}
	UNITTEST_QUIET=true
	assertOutputEqual 'unittest::run custom_test' 'executed'
}

selftest_execute_setUp() {
	setUp() {
		echo 'setup'
	}
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	UNITTEST_QUIET=true
	assertOutputEqual unittest::run "setup\nfirst\nsetup\nsecond"
}

selftest_execute_tearDown() {
	tearDown() {
		echo 'teardown'
	}
	test_first() {
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	UNITTEST_QUIET=true
	assertOutputEqual unittest::run "first\nteardown\nsecond\nteardown"
}

selftest_execute_tearDown_on_unexpected_exit() {
	setUp() {
		echo 'setup'
	}
	tearDown() {
		echo 'teardown'
	}
	test_first() {
		exit 1
		echo 'first'
	}
	test_second() {
		echo 'second'
	}
	UNITTEST_QUIET=true
	assertOutputEqual unittest::run "setup\nteardown\nsetup\nsecond\nteardown"
}

selftest_forget_internal_environment() {
	[ -z "$UNITTEST_EXPORTED_VALUE" ] || panic '$UNITTEST_EXPORTED_VALUE is present in env, cannot reuse for testing purposes!'
	test_first() {
		export UNITTEST_EXPORTED_VALUE=1
	}
	UNITTEST_QUIET=true
	unittest::run
	assertStringEmpty "$UNITTEST_EXPORTED_VALUE"
}

selftest_print_unittest_run_stats() {
	test_first() {
		true
	}
	test_second() {
		true
	}
	assertOutputEqual 'unittest::run 2>&1' "Executed: 2 test(s).\nSuccessful: 2 test(s).\nOK"
}

selftest_display_failure_count() {
	test_first() {
		true
	}
	test_second() {
		false
	}
	assertOutputEqual 'unittest::run 2>&1' "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 test(s).\nFAIL"
}

selftest_assert_files_same() {
	FIRST_TMPFILE=$(mktemp)
	SECOND_TMPFILE=$(mktemp)
	test_same() {
		trap "rm -f '$FIRST_TMPFILE' '$SECOND_TMPFILE'" EXIT
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "a\nb" >"$SECOND_TMPFILE"
		assertFilesSame "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}
	test_differ() {
		trap "rm -f '$FIRST_TMPFILE' '$SECOND_TMPFILE'" EXIT
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "c\nb" >"$SECOND_TMPFILE"
		assertFilesSame "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_differ: Assert failed:
Files are not the same:
--- $FIRST_TMPFILE
+++ $SECOND_TMPFILE
@@ -1,2 +1,2 @@
-a
+c
 b
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_files_different() {
	FIRST_TMPFILE=$(mktemp)
	SECOND_TMPFILE=$(mktemp)
	test_same() {
		trap "rm -f '$FIRST_TMPFILE' '$SECOND_TMPFILE'" EXIT
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "a\nb" >"$SECOND_TMPFILE"
		assertFilesDiffer "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}
	test_differ() {
		trap "rm -f '$FIRST_TMPFILE' '$SECOND_TMPFILE'" EXIT
		echo -e "a\nb" >"$FIRST_TMPFILE"
		echo -e "c\nb" >"$SECOND_TMPFILE"
		assertFilesDiffer "$FIRST_TMPFILE" "$SECOND_TMPFILE"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-9)):test_same: Assert failed:
Files do not differ:
--- $FIRST_TMPFILE
+++ $SECOND_TMPFILE
a
b
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_strings_equal() {
	test_same() {
		FIRST='first'
		SECOND='first'
		assertStringsEqual "$FIRST" "$SECOND"
	}
	test_differ() {
		FIRST='first'
		SECOND='second'
		assertStringsEqual "$FIRST" "$SECOND"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_differ: Assert failed:
Strings are not equal:
Expected: 'first'
Actual: 'second'
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_strings_not_equal() {
	test_same() {
		FIRST='first'
		SECOND='first'
		assertStringsNotEqual "$FIRST" "$SECOND"
	}
	test_differ() {
		FIRST='first'
		SECOND='second'
		assertStringsNotEqual "$FIRST" "$SECOND"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-8)):test_same: Assert failed:
Strings do not differ:
'first'
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_string_empty() {
	test_empty() {
		assertStringEmpty ""
	}
	test_not_empty() {
		assertStringEmpty "content"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_not_empty: Assert failed:
String is not empty:
'content'
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_string_not_empty() {
	test_empty() {
		assertStringNotEmpty ""
	}
	test_not_empty() {
		assertStringNotEmpty "content"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-6)):test_empty: Assert failed:
String is empty!
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_output_equal() {
	test_same() {
		assertOutputEqual 'echo -e "first\nsecond"' "first\nsecond"
	}
	test_differs() {
		assertOutputEqual 'echo -e "first\nsecond"' "differs"
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_differs: Assert failed:
Command output differs:
echo -e "first\nsecond"
--- [expected]
+++ [actual]
@@ -1 +1,2 @@
-differs
+first
+second
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_output_equal_stdin() {
	test_same() {
		echo -e "first\nsecond" | assertOutputEqual 'echo -e "first\nsecond"' -
	}
	test_dash_on_stdin() {
		echo -- - | assertOutputEqual 'echo -- -' -
	}
	test_differs() {
		echo "differs" | assertOutputEqual 'echo -e "first\nsecond"' -
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_differs: Assert failed:
Command output differs:
echo -e "first\nsecond"
--- [expected]
+++ [actual]
@@ -1 +1,2 @@
-differs
+first
+second
Executed: 3 test(s).
Successful: 2 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_return_code_of_previous_command_assert() {
	test_ok() {
		assertOutputEqual 'echo test; exit 1' 'test'
		assertReturnCode 1
	}
	test_fail() {
		assertOutputEqual 'echo test; exit 1' 'test'
		assertReturnCode 0
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_fail: Assert failed:
Command return code differs:
echo test; exit 1
Expected: 0
Actual: 1
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_return_code() {
	test_same() {
		assertReturnCode 1 'exit 1'
	}
	test_differs() {
		assertReturnCode 1 'exit 0'
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_differs: Assert failed:
Command return code differs:
exit 0
Expected: 1
Actual: 0
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_exit_success() {
	test_success() {
		assertExitSuccess 'exit 0'
	}
	test_failure() {
		assertExitSuccess 'exit 1'
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-3)):test_failure: Assert failed:
Command did not exit with success:
exit 1
Actual exit code: 1
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_exit_failure() {
	test_success() {
		assertExitFailure 'exit 0'
	}
	test_failure() {
		assertExitFailure 'exit 1'
	}

	assertOutputEqual 'unittest::run 2>&1' - <<EOF
$0:$(($LINENO-6)):test_success: Assert failed:
Command did not exit with failure:
exit 0
Actual exit code: 0
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

unittest::run selftest_
