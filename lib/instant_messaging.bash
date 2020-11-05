#!/bin/bash

pidgin::_enum_windows() {
	# Prints windows IDs to stdout.
	pgrep -x pidgin | while read pid; do
		wmctrl -l -p | grep ${pid} | awk '{print $1}'
	done
}

pidgin::messages::get() {
	# Prints total unread messages in ALL Pidgin windows.
	pidgin::_enum_windows | while read window; do
		xprop -id ${window} | grep _PIDGIN_UNSEEN_COUNT | awk '{print $NF}'
	done | paste -sd+ | bc
}

pidgin::messages::set() { # <new value>
	# Sets total unread messages in ALL Pidgin windows to specified value.
	pidgin::_enum_windows | while read window; do
		xprop -id ${window} -format _PIDGIN_UNSEEN_COUNT 32c -set _PIDGIN_UNSEEN_COUNT "$1"
	done
}

pidgin::messages::inc() {
	# Increases total unread messages in ALL Pidgin windows by 1.
	pidgin::_enum_windows | while read window; do
		value=$(xprop -id ${window} | grep _PIDGIN_UNSEEN_COUNT | awk '{print $NF}')
		xprop -id ${window} -format _PIDGIN_UNSEEN_COUNT 32c -set _PIDGIN_UNSEEN_COUNT $((value+1))
	done
}

pidgin::messages::dec() {
	# Decreases total unread messages in ALL Pidgin windows by 1.
	pidgin::_enum_windows | while read window; do
		value=$(xprop -id ${window} | grep _PIDGIN_UNSEEN_COUNT | awk '{print $NF}')
		[ "$value" == 0 ] && continue
		xprop -id ${window} -format _PIDGIN_UNSEEN_COUNT 32c -set _PIDGIN_UNSEEN_COUNT $((value-1))
	done
}

