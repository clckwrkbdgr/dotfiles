#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

should_for_miniclick_parse_arguments_as_positionals() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	test_click() {
		click::miniclick 'short' 'long' 'name' -- 'default' 'help' -- "$@"
		echo "short=<$short>"
		echo "long=<$long>"
		echo "name=<$name>"
		echo "default=<$default>"
		echo "help=<$help>"
	}
	assertOutputEqual 'test_click -o --option option_name default_value help_message 2>&1' - <<EOF
short=<-o>
long=<--option>
name=<option_name>
default=<default_value>
help=<help_message>
EOF
}

should_for_miniclick_parse_arguments_with_dashes() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	test_click() {
		click::miniclick 'short' 'long' 'name' -- 'default' 'help' -- "$@"
		echo "short=<$short>"
		echo "long=<$long>"
		echo "name=<$name>"
		echo "default=<$default>"
		echo "help=<$help>"
	}
	assertOutputEqual 'test_click -o --option option_name --help=help_message --default=default_value 2>&1' - <<EOF
short=<-o>
long=<--option>
name=<option_name>
default=<default_value>
help=<help_message>
EOF
}

should_for_miniclick_ignore_missing_parameters() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	short=DEFAULT
	long=DEFAULT
	name=DEFAULT
	default=DEFAULT
	help=DEFAULT
	test_click() {
		click::miniclick 'short' 'long' 'name' -- 'default' 'help' -- "$@"
		echo "short=<$short>"
		echo "long=<$long>"
		echo "name=<$name>"
		echo "default=<$default>"
		echo "help=<$help>"
	}
	assertOutputEqual 'test_click -o --option 2>&1' - <<EOF
short=<-o>
long=<--option>
name=<>
default=<>
help=<>
EOF
}

should_for_miniclick_panic_on_unknown_positionals() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	test_click() {
		click::miniclick 'short' 'long' 'name' -- 'default' 'help' -- "$@"
	}
	assertOutputEqual 'test_click -o --option option_name --help=help_message default_value override_help_message extra 2>&1' - <<EOF
${BASH_SOURCE[0]}:74:test_click: miniclick: unknown unnamed param: 'extra'
EOF
}

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

should_process_additional_parameters_of_definitions_of_arguments() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::flag -f --flag '' --help='Flag help'
	click::option -o --option option_name --default=default_value --help='Option help'
	click::argument arg --help='Argument help'
	test_click() {
		:
	}
	assertOutputEqual 'click::run -h 2>&1' - <<EOF
Usage: $0 [-o] [-f] <arg>
Parameters:
  -o, --option
        Option help
        Default is 'default_value'.
  -f, --flag
        Flag help
        Default is false.
  <arg>
        Argument help
EOF
}


unittest::run should_
