#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

selftest_execute_single_test() {
	test_test() {
		echo 'executed'
	}
	UNITTEST_QUIET=true
	output=$(FORCE_SOURCED_UNITTESTS=1 unittest::run)
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
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run' "first\nsecond"
}

selftest_custom_test_prefix() {
	custom_test_test() {
		echo 'executed'
	}
	UNITTEST_QUIET=true
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run custom_test' 'executed'
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
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run' "setup\nfirst\nsetup\nsecond"
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
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run' "first\nteardown\nsecond\nteardown"
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
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run' "setup\nteardown\nsetup\nsecond\nteardown"
}

selftest_forget_internal_environment() {
	[ -z "$UNITTEST_EXPORTED_VALUE" ] || panic '$UNITTEST_EXPORTED_VALUE is present in env, cannot reuse for testing purposes!'
	test_first() {
		export UNITTEST_EXPORTED_VALUE=1
	}
	UNITTEST_QUIET=true
	FORCE_SOURCED_UNITTESTS=1 unittest::run
	assertStringEmpty "$UNITTEST_EXPORTED_VALUE"
}

selftest_print_unittest_run_stats() {
	export UNITTEST_QUIET=
	test_first() {
		true
	}
	test_second() {
		true
	}
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' "Executed: 2 test(s).\nSuccessful: 2 test(s).\nOK"
}

selftest_display_failure_count() {
	export UNITTEST_QUIET=
	test_first() {
		true
	}
	test_second() {
		false
	}
	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' "Executed: 2 test(s).\nSuccessful: 1 test(s).\nFailures: 1 test(s).\nFAIL"
}

selftest_assert_files_same() {
   fix_msys_paths=cat
   if [ "$(uname -o)" == Msys ]; then
      fix_msys_paths="sed 's|C:/Users/.*/AppData/Local/Temp|/tmp|'"
   fi

	export UNITTEST_QUIET=
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

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1 | '"$fix_msys_paths" - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_differ: Assert failed:
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
	export UNITTEST_QUIET=
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

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-9)):test_same: Assert failed:
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
	export UNITTEST_QUIET=
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

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_differ: Assert failed:
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
	export UNITTEST_QUIET=
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

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-8)):test_same: Assert failed:
Strings do not differ:
'first'
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_string_empty() {
	export UNITTEST_QUIET=
	test_empty() {
		assertStringEmpty ""
	}
	test_not_empty() {
		assertStringEmpty "content"
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_not_empty: Assert failed:
String is not empty:
'content'
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_string_not_empty() {
	export UNITTEST_QUIET=
	test_empty() {
		assertStringNotEmpty ""
	}
	test_not_empty() {
		assertStringNotEmpty "content"
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-6)):test_empty: Assert failed:
String is empty!
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_output_equal() {
	export UNITTEST_QUIET=
	test_same() {
		assertOutputEqual 'echo -e "first\nsecond"' "first\nsecond"
	}
	test_differs() {
		assertOutputEqual 'echo -e "first\nsecond"' "differs"
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_differs: Assert failed:
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

selftest_assert_output_empty() {
	export UNITTEST_QUIET=
	test_empty() {
		assertOutputEmpty 'echo -n ""'
	}
	test_not_empty() {
		assertOutputEmpty 'echo ""'
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_not_empty: Assert failed:
Command output is not empty:
echo ""
--- [expected: empty]
+++ [actual]
@@ -0,0 +1 @@
+
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_assert_output_equal_stdin() {
	export UNITTEST_QUIET=
	test_same() {
		echo -e "first\nsecond" | assertOutputEqual 'echo -e "first\nsecond"' -
	}
	test_dash_on_stdin() {
		echo -- - | assertOutputEqual 'echo -- -' -
	}
	test_differs() {
		echo "differs" | assertOutputEqual 'echo -e "first\nsecond"' -
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_differs: Assert failed:
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
	export UNITTEST_QUIET=
	test_ok() {
		assertOutputEqual 'echo test; exit 1' 'test'
		assertReturnCode 1
	}
	test_fail() {
		assertOutputEqual 'echo test; exit 1' 'test'
		assertReturnCode 0
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_fail: Assert failed:
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
	export UNITTEST_QUIET=
	test_same() {
		assertReturnCode 1 'exit 1'
	}
	test_differs() {
		assertReturnCode 1 'exit 0'
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_differs: Assert failed:
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
	export UNITTEST_QUIET=
	test_success() {
		assertExitSuccess 'exit 0'
	}
	test_failure() {
		assertExitSuccess 'exit 1'
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-3)):test_failure: Assert failed:
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
	export UNITTEST_QUIET=
	test_success() {
		assertExitFailure 'exit 0'
	}
	test_failure() {
		assertExitFailure 'exit 1'
	}

	assertOutputEqual 'FORCE_SOURCED_UNITTESTS=1 unittest::run 2>&1' - <<EOF
${BASH_SOURCE[0]}:$(($LINENO-6)):test_success: Assert failed:
Command did not exit with failure:
exit 0
Actual exit code: 0
Executed: 2 test(s).
Successful: 1 test(s).
Failures: 1 test(s).
FAIL
EOF
}

selftest_skip_test_runner_in_sourced_files() {
	tmpsource=$(mktemp)
	tmpscript=$(mktemp)
	finally "rm -f '$tmpsource' '$tmpscript'"
	cat >"$tmpsource" <<EOF
#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
test_case() {
	assertStringsEqual A not-A
}
export UNITTEST_QUIET=
unittest::run test_
EOF
	cat >"$tmpscript" <<EOF
. "$tmpsource"
EOF
	chmod +x "$tmpscript"

	assertOutputEmpty "'$tmpscript' 2>&1"
}

selftest_list_defined_test_cases() {
	tmpsource=$(mktemp)
	finally "rm -f '$tmpsource'"
	cat >"$tmpsource" <<EOF
#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
test_success() {
	assertExitSuccess 'exit 0'
}
test_failure() {
	assertExitSuccess 'exit 1'
}
export UNITTEST_QUIET=
unittest::run
EOF

	assertOutputEqual "unittest::list '$tmpsource' 2>&1" - <<EOF
test_failure
test_success
EOF

	cat >"$tmpsource" <<EOF
#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
should_ignore_previous_tests() {
	assertExitSuccess 'exit 0'
}
export UNITTEST_QUIET=
unittest::run should_
EOF

	assertOutputEqual "unittest::list '$tmpsource' 2>&1" - <<EOF
should_ignore_previous_tests
EOF
}

selftest_list_defined_test_cases_in_current_scope() {
	tmpsource=$(mktemp)
	finally "rm -f '$tmpsource'"
	cat >"$tmpsource" <<EOF
#!/bin/bash
. "$XDG_CONFIG_HOME/lib/unittest.bash"
test_success() {
	assertExitSuccess 'exit 0'
}
test_failure() {
	assertExitSuccess 'exit 1'
}
export UNITTEST_QUIET=
unittest::run

unittest::list
EOF

	assertOutputEqual ". '$tmpsource' 2>&1" - <<EOF
test_failure
test_success
EOF
}

unittest::run selftest_
