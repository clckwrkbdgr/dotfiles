#!/bin/bash
. "$XDG_CONFIG_HOME/lib/utils.bash"

set -o pipefail
# TODO unit-testing framework for bash

TMPFILE="/tmp/test_click.txt"
trap 'rm -f "$TMPFILE"' EXIT

(
. "$XDG_CONFIG_HOME/lib/click.bash"

click::command test_click 'Description.'
test_click() {
	:
}
cat >"$TMPFILE" <<EOF
Usage: test/test_click.bash
Description.
EOF
click::run -h 2>&1 | diff "$TMPFILE" -
) || panic 'Differs.'

(
. "$XDG_CONFIG_HOME/lib/click.bash"

cat >"$TMPFILE" <<EOF
Short flag is required!
EOF
	click::flag 2>&1 | diff "$TMPFILE" -
) && panic 'RC is 1'

(
. "$XDG_CONFIG_HOME/lib/click.bash"

cat >"$TMPFILE" <<EOF
Expected short flag in format '-<single char>', got instead: 'a'
EOF
	click::flag 'a' 2>&1 | diff "$TMPFILE" -
) && panic 'RC is 1'

(
. "$XDG_CONFIG_HOME/lib/click.bash"

cat >"$TMPFILE" <<EOF
Expected long flag in format '--<name>', got instead: 'no-dashes'
EOF
	click::flag '-a' 'no-dashes' 2>&1 | diff "$TMPFILE" -
) && panic 'RC is 1'

(
. "$XDG_CONFIG_HOME/lib/click.bash"

click::command test_click
click::option '-o' '--option' 
click::flag '-f' '--flag' 
click::argument 'name'
test_click() {
	[ -n "${CLICK_ARGS[flag]}" ] || panic 'flag is false'
	[ "${CLICK_ARGS[option]}" == option_value ] || panic option_value
	[ "${CLICK_ARGS[name]}" == argument_value ] || panic argument_value
}

click::run -o option_value -f argument_value
) || panic 'RC is not 0'

(
. "$XDG_CONFIG_HOME/lib/click.bash"

click::command test_click
click::argument 'first'
click::argument 'second'
click::argument 'third'
test_click() {
	[ "${CLICK_ARGS[first]}" == arg1 ] || panic arg1
	[ "${CLICK_ARGS[second]}" == arg2 ] || panic arg2
	[ "${CLICK_ARGS[third]}" == arg3 ] || panic arg3
}

click::run arg1 arg2 arg3
) || panic 'RC is not 0'

