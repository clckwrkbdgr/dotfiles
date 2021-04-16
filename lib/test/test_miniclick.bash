#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"
. "$XDG_CONFIG_HOME/lib/unittest.bash"

should_parse_arguments_as_positionals() {
	. "$XDG_CONFIG_HOME/lib/miniclick.bash"

	test_click() {
		miniclick short long name --default --help -- "$@"
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

should_parse_arguments_with_dashes() {
	. "$XDG_CONFIG_HOME/lib/miniclick.bash"

	test_click() {
		miniclick short long name --default --help -- "$@"
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

should_ignore_missing_parameters() {
	. "$XDG_CONFIG_HOME/lib/miniclick.bash"

	short=DEFAULT
	long=DEFAULT
	name=DEFAULT
	unset default
	help=DEFAULT
	test_click() {
		miniclick short long name --default --help -- "$@"
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

should_panic_on_unknown_positionals() {
	. "$XDG_CONFIG_HOME/lib/miniclick.bash"

	test_click() {
		miniclick short long name --default --help -- "$@"
	}
	assertOutputEqual 'test_click -o --option option_name --help=help_message default_value override_help_message extra 2>&1' - <<EOF
${BASH_SOURCE[0]}:74:test_click: miniclick: unknown unnamed param: 'extra'
EOF
}

should_parse_arguments_with_apostrophes() {
	. "$XDG_CONFIG_HOME/lib/miniclick.bash"

	test_click() {
		miniclick text -- "$@"
		echo "$text"
	}
	assertOutputEqual 'test_click "I'"'"'m in space" 2>&1' - <<EOF
I'm in space
EOF
}

unittest::run should_
