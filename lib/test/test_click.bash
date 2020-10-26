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
	unset default
	help=DEFAULT
	test_click() {
		click::miniclick 'short' 'long' 'name' -- 'default' 'help' -- "$@"
		echo "short=<$short>"
		echo "long=<$long>"
		echo "name=<$name>"
		[ -z "${default+unset}" ] && echo "default=<unset>"
		echo "help=<$help>"
	}
	assertOutputEqual 'test_click -o --option 2>&1' - <<EOF
short=<-o>
long=<--option>
name=<>
default=<unset>
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

should_consume_all_positionals_for_nargs() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second'
	click::argument 'third' --nargs=-1
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'arg1'
		assertStringsEqual "${CLICK_ARGS[second]}" 'arg2'
		assertStringsEqual "${CLICK_ARGS[third]}" 'arg3 arg3.1 arg3.2'
		assertStringsEqual "${#CLICK_NARGS[@]}" 3
		assertStringsEqual "${CLICK_NARGS[0]}" 'arg3'
		assertStringsEqual "${CLICK_NARGS[1]}" 'arg3.1'
		assertStringsEqual "${CLICK_NARGS[2]}" 'arg3.2'
	}

	assertExitSuccess 'click::run arg1 arg2 arg3 arg3.1 arg3.2'
}

should_consume_even_arguments_with_dash_for_nargs() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second'
	click::argument 'third' --nargs=-1
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'arg1'
		assertStringsEqual "${CLICK_ARGS[second]}" 'arg2'
		assertStringsEqual "${CLICK_ARGS[third]}" 'arg3 --arg3.1 -arg3.2'
		assertStringsEqual "${#CLICK_NARGS[@]}" 3
		assertStringsEqual "${CLICK_NARGS[0]}" 'arg3'
		assertStringsEqual "${CLICK_NARGS[1]}" '--arg3.1'
		assertStringsEqual "${CLICK_NARGS[2]}" '-arg3.2'
	}

	assertExitSuccess 'click::run arg1 arg2 arg3 --arg3.1 -arg3.2'
}

should_allow_zero_given_arguments_for_nargs() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second'
	click::argument 'third' --nargs=-1
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'arg1'
		assertStringsEqual "${CLICK_ARGS[second]}" 'arg2'
		assertStringsEqual "${#CLICK_NARGS[@]}" 0
		assertStringsEqual "${CLICK_ARGS[third]}" ''
	}

	assertExitSuccess 'click::run arg1 arg2'
}

should_allow_only_negative_one_nargs() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	assertOutputEqual "click::argument 'second' --nargs=1 2>&1" - <<EOF
Parameter nargs supports only value -1 for arguments: second nargs=1
EOF
	assertReturnCode 1
}

should_allow_nargs_positional_only_at_the_end() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second' --nargs=-1
	assertOutputEqual "click::argument 'third' 2>&1" - <<EOF
There was already defined an argument with nargs=-1: second
EOF
	assertReturnCode 1
}

should_allow_default_value_for_positionals() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second' --default=default
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'value'
		assertStringsEqual "${CLICK_ARGS[second]}" 'default'
	}

	assertExitSuccess 'click::run value'
}

should_allow_empty_default_value_for_positionals() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first'
	click::argument 'second' --default=''
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'value'
		assertStringsEqual "${CLICK_ARGS[second]}" ''
	}

	assertExitSuccess 'click::run value'
}

should_allow_default_value_for_positionals_only_at_the_end() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first' --default=default
	click::argument 'second'
	test_click() {
		:
	}

	assertOutputEqual "click::run 'value' 2>&1" - <<EOF
Positional argument is expected: 'second'
EOF
	assertReturnCode 1
}

should_allow_default_values_for_several_tailing_positionals() {
	. "$XDG_CONFIG_HOME/lib/click.bash"

	click::command test_click
	click::argument 'first' --default=default_first
	click::argument 'second' --default=default_second
	test_click() {
		assertStringsEqual "${CLICK_ARGS[first]}" 'default_first'
		assertStringsEqual "${CLICK_ARGS[second]}" 'default_second'
	}

	assertExitSuccess 'click::run'
}

unittest::run should_
