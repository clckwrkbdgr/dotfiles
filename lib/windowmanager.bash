#!/bin/bash

processes_by_names() { # <list of pnames>
	# Prints PIDs of all processes that match given list of patterns.
	for pname in "$@"; do
		pgrep "$pname"
	done
}

get_current_desktop() {
	# Prints index of current desktop workspace.
	wmctrl -d | awk '{ if ($2 == "*") print $1 }'
}

windows_and_desktops_by_pid() { # <pid...>
	# Finds and prints windows IDs opened by given PID(s).
	# Only windows placed on real desktop space are printed.
	# Yields in pairs: first line is <window_id>, second line is <desktop_number>
	for pid in "$@"; do
		xdotool search --pid "$pid" | while read window_id; do
			window_name="$(xdotool getwindowname $window_id)"
			if [ -z "$window_name" ]; then
				continue
			fi
			desktop_number=$(xprop -id "$window_id" | grep _NET_WM_DESKTOP | sed 's/.*= *//')
			if [ -n "$desktop_number" ]; then
				echo $window_id
				echo "$desktop_number"
			fi
		done
	done
}

windows_by_pid() { # <pid...>
	# Finds and prints just windows IDs (for all desktops) opened by given PID(s).
	windows_and_desktops_by_pid "$@" | while read window_id; do
		echo "$window_id"
		read desktop_id # And skip.
	done
}

windows_by_pid_on_current_desktop() { # <pid...>
	# Finds and prints just windows IDs (for current desktop only) opened by given PID(s).
	current_desktop=$(get_current_desktop)
	windows_and_desktops_by_pid "$@" | while read window_id; do
		read desktop_id
		if [ "$desktop_id" == "$current_desktop" ]; then
			echo "$window_id"
		fi
	done
}

bring_to_top() { # <window_id>
	# Brings to top window by given ID.
	window_id="$1"
	xdotool windowactivate "$window_id"
}

bring_to_top_by_pnames() { # <process name>
	# Brings to top the most recent opened window of all windows associated with list of process names
	# Tries to find window on current desktop, and if there's no such windows, finds any window on any desktop.
	processes_by_names "$@" | while read pid; do
		windows_by_pid "$pid"
		windows_by_pid_on_current_desktop "$pid"
	done | tail -1 | while read window_id; do
		if bring_to_top "$window_id"; then
			return 0
		fi
	done
	return 1
}
