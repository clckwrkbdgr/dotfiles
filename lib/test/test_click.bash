#!/bin/bash
. "$XDG_CONFIG_HOME/lib/click.bash"

# TODO unit-testing framework for bash
click::command test_click
click::option '-o' '--option' 
click::flag '-f' '--flag' 
click::argument 'name'
test_click() {
	[ -n "${CLICK_ARGS[flag]}" ] || panic 'flag is false'
	[ "${CLICK_ARGS[option]}" == option_value ] || panic option_value
	[ "${CLICK_ARGS[name]}" == argument_value ] || panic argument_value
}

(
	click::run -o option_value -f argument_value
	) || panic 'RC is not 0'
