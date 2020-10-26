#!/bin/bash

processes_by_names() { # <list of pnames>
	# Prints PIDs of all processes that match given list of patterns.
	for pname in "$@"; do
		pgrep "$pname"
	done
}

windows_by_pid() { # <pid...>
	# Finds and prints windows IDs opened by given PID(s).
	for pid in "$@"; do
		xdotool search --pid "$pid" | while read window_id; do
			window_name="$(xdotool getwindowname $window_id)"
			if [ -z "$window_name" ]; then
				continue
			fi
			if xprop -id "$window_id" | grep -q _NET_WM_DESKTOP; then
				echo $window_id
			fi
		done
	done
}

bring_to_top() { # <window_id>
	# Brings to top window by given ID.
	window_id="$1"
	xdotool windowactivate "$window_id"
}

bring_to_top_by_pnames() { # <process name>
	# Brings to top the most recent opened window of all windows associated with list of process names
	processes_by_names "$@" | while read pid; do
		windows_by_pid "$pid"
	done | tail -1 | while read window_id; do
		if bring_to_top "$window_id"; then
			return 0
		fi
	done
	return 1
}
