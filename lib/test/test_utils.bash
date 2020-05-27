. "$XDG_CONFIG_HOME/lib/unittest.bash"
. "$XDG_CONFIG_HOME/lib/utils.bash"

should_panic() {
	assertOutputEqual 'panic "ERROR" 2>&1; echo "this should not happen"' 'ERROR'
	assertExitFailure
}

unittest::run should_
