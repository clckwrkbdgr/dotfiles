. "$XDG_CONFIG_HOME/lib/unittest.bash"
. "$XDG_CONFIG_HOME/lib/utils.bash"

should_panic() {
	assertOutputEqual 'panic "ERROR" 2>&1; echo "this should not happen"' 'ERROR'
	assertExitFailure
}

should_perform_actions_finally() {
	assertOutputEqual "( finally 'echo finally'; echo 'test' )" "test\nfinally"
}

should_accumulate_finally_statements() {
	assertOutputEqual "( finally 'echo first finally'; echo 'test'; finally 'echo second finally';  )" "test\nfirst finally\nsecond finally"
}

should_perform_finally_in_separate_subshells_independently() {
	assertOutputEqual "( finally 'echo first'; echo 'test' )" "test\nfirst"
	assertOutputEqual "( finally 'echo second'; echo 'test' )" "test\nsecond"
}


unittest::run should_
