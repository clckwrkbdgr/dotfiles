#!/bin/bash

get_parent_process() { # <pid>
	# Finds and prints parent process ID.
	ps --no-header -o ppid $1 | tr -d ' '
}

find_subprocess() { # <pattern> [<process ID>]
	# Finds and prints subprocesses that contain pattern in command line.
	# If process ID is omitted, by default current process is used.
	pattern=$1
	pid=${2:-$$}
	ps -o pid,args --ppid "$pid" | grep "$pattern" | awk '{print $1}'
}

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
			desktop_number=$(xprop -id "$window_id" | grep '^_NET_WM_DESKTOP' | sed 's/.*= *//')
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

await_process_window() { # <process search command line> <wait seconds for process> <wait seconds for window>
	# Waits for the process to start and then for any window to appear, prints ID of that window.
	# First argument is a command line that should print the desired PID, e.g. 'pgrep my_process'
	# If any action fails after corresponding waiting interval is over, returns failure.
	search_command=${1:-echo $$}
	wait_process=${2:-3}
	wait_window=${3:-3}

	pid=$(eval "$search_command")
	counter=${wait_process}0
	while [ -z "$pid" -a $counter -gt 0 ]; do
		pid=$(eval "$search_command")
		sleep 0.1
		counter=$((counter-1))
	done
	[ -z "$pid" ] && return 1
	counter=${wait_window}0
	window_id=$(xdotool search --pid $pid)
	while [ -z "$window_id" -a $counter -gt 0 ]; do
		window_id=$(xdotool search --pid $pid)
		sleep 0.1
		counter=$((counter-1))
	done
	[ -z "$window_id" ] && return 1
	echo "$window_id"
}

find_parent_x_window() { # <pid>
	# Finds the first process in the tree that has X window attached.
	# It may include the current process as well.
	# Prints ID (decimal) of the first window for the found process.
	current_pid=$1
	window_id=
	while [ -n "$current_pid" ] && [ -z "$window_id" ]; do
		current_pid=$(get_parent_process $current_pid)
		window_id=$(xdotool search --pid "$current_pid" | head -1)
	done
	echo "$window_id"
}

find_process_desktop_id() { # <pid>
	# Finds and prints which virtual desktop (decimal) runs the given process.
	window_id=$(find_parent_x_window $1)
	xprop -id "$window_id" -format _NET_WM_DESKTOP 32c '|$0+' _NET_WM_DESKTOP | sed 's/^[^|]*|//'
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

change_window_class() { # <window id> <new_class_name>
	window_id="$1"
	new_class_name="$2"
	xprop -id "$window_id" -format WM_CLASS 8s -set WM_CLASS "$new_class_name"
}

make_background_window() { # <window class>
	# Removes window from taskbark and maximizes it.
	window_class="$1"
	while ! wmctrl -R "$window_class" -x -b add,skip_taskbar ; do :; done
	wmctrl -R "$window_class" -x -b remove,sticky
	wmctrl -R "$window_class" -x -b add,maximized_vert,maximized_horz
}

get_window_class() { # <window_id>
	window_id="$1"
	xprop -id "$window_id" WM_CLASS | cut -d '"' -f 2
}

roll_window_out() { # <window_id> <speed>
	# Shows window with rolling animation.
	# Gives focus to the window immediately.
	# Maximizes window at the end of the sequence.
	window_id="$1"
	speed="${2:-10}"

	screen_height=$(xdpyinfo | grep dimensions | awk '{print $2}' | awk -Fx '{print $2}')
	animation_count=$((screen_height / speed))
	for i in `seq $animation_count -1 1`; do
		pos=$(($i * $speed))
		xdotool windowmove "$window_id" "-$speed" -${pos}
	done
	window_class="$(get_window_class "$window_id")"
	wmctrl -R "$window_class" -x -b add,maximized_vert,maximized_horz
}

roll_window_in() { # <window_id> <speed>
	# Hides window with rolling animation.
	# Minimizes window at the end of the sequence.
	window_id="$1"
	speed="${2:-10}"

	if xprop -id "$window_id" -notype "QUAKESTYLE_MINIMIZED" | grep TRUE; then
		return
	fi
	xprop -id "$window_id" -f QUAKESTYLE_MINIMIZED 8s -set "QUAKESTYLE_MINIMIZED" TRUE

	wmctrl -R "$window_class" -x -b remove,maximized_vert,maximized_horz
	xdotool windowsize "$window_id" 100% 100%

	screen_height=$(xdpyinfo | grep dimensions | awk '{print $2}' | awk -Fx '{print $2}')
	animation_count=$((screen_height / speed))
	for i in `seq 1 $animation_count`; do
		pos=$(($i * $speed))
		xdotool windowmove "$window_id" -3 -${pos}
	done
	xdotool windowminimize "$window_id"

	xprop -id "$active_window_id" -f QUAKESTYLE_MINIMIZED 8s -set "QUAKESTYLE_MINIMIZED" FALSE
}
