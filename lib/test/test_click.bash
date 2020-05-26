#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

should_print_usage_info() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click 'Description.'
	test_click() {
		:
	}
	assertOutputEqual 'click::run -h 2>&1' - <<EOF
Usage: $0
Description.
EOF
}

should_fail_when_short_flag_is_missing() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	assertOutputEqual 'click::flag 2>&1' -  <<EOF
Short flag is required!
EOF
	assertReturnCode 1
}

should_fail_if_flag_does_not_start_with_single_dash() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	assertOutputEqual "click::flag 'a' 2>&1" -<<EOF
Expected short flag in format '-<single char>', got instead: 'a'
EOF
	assertReturnCode 1
}

should_fail_if_long_flag_does_not_start_with_dashes() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	assertOutputEqual "click::flag '-a' 'no-dashes' 2>&1" - <<EOF
Expected long flag in format '--<name>', got instead: 'no-dashes'
EOF
	assertReturnCode 1
}

should_parse_options_and_flags() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::option '-o' '--option' 
	click::flag '-f' '--flag' 
	click::argument 'name'
	test_click() {
		assertStringNotEmpty "${CLICK_ARGS[flag]}"
		assertStringsEqual "${CLICK_ARGS[option]}" 'option_value'
		assertStringsEqual "${CLICK_ARGS[name]}" 'argument_value'
	}

	assertExitSuccess 'click::run -o option_value -f argument_value'
}

should_parse_positionals() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second'
	click::argument 'third'
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'arg1'
		assertStringsEqual "${CLICK_ARGS[second]}" 'arg2'
		assertStringsEqual "${CLICK_ARGS[third]}" 'arg3'
	}

	assertExitSuccess 'click::run arg1 arg2 arg3'
}

unittest::run should_
