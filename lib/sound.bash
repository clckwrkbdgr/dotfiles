#!/bin/bash

current_volume() {
	# Prints current volume value to stdout in percents (without the percent sign).
	# If argument is supplied, this channel is checked. Default channel is 'Master'.
	channel="${1:-Master}"
	if amixer get "$channel" | grep -q 'Front Left'; then
		amixer get "$channel" | sed '/^ *Front\ Left: /{s/^.*\[\(.*\)%\].*/\1/;p;};d;'
	else
		amixer get "$channel" | sed '/^ *Mono: Playback /{s/^.*\[\(.*\)%\].*/\1/;p;};d;'
	fi
}

current_channel_status() {
	# Prints current status of channel to stdout ([on] or [off]).
	# If argument is supplied, this channel is checked. Default channel is 'Master'.
	channel="${1:-Master}"
	if amixer get "$channel" | grep -q 'Front Left'; then
		amixer get "$channel" | awk '$2 == "Left:" { print $NF; }'
	else
		amixer get "$channel" | sed '/^ *Mono: Playback /{s/^.*\[\(.*\)\]$/\1/;p;};d;'
	fi
}

set_volume() {
	# Usage: [<channel>] <volume>
	# Sets volume for specified channel.
	# If channel is skipped, default 'Master' is used.
	# Volume should be integer in range 0..150
	channel="$1"
	volume="$2"
	if [ -z "$volume" ]; then
		volume="$channel"
		channel='Master'
	fi
	if [ "$volume" -lt 0 -o "$volume" -gt 150 ]; then
		echo "Invalid volume level: $volume, expected to be in range of 0..150" >&2
		return 1
	fi
	if [ "$volume" -lt 100 ]; then
		amixer set "$channel" ${volume}% >/dev/null
	else
		channel=$(LANG=C pactl list | grep '^Sink #' | sed 's/.* #//')
		pactl set-sink-volume ${channel:-0} ${volume}%
	fi
	return 0
}

volume_up() {
	# Usage: [<channel>] <step>
	# Ups volume for specified channel and specified step (in percents without percent sign).
	# If channel is skipped, default 'Master' is used.
	channel="$1"
	step="$2"
	if [ -z "$step" ]; then
		step="$channel"
		channel='Master'
	fi
	amixer set "$channel" "${step}%+" >/dev/null
}

volume_down() {
	# Usage: [<channel>] <step>
	# Downs volume for specified channel and specified step (in percents without percent sign).
	# If channel is skipped, default 'Master' is used.
	channel="$1"
	step="$2"
	if [ -z "$step" ]; then
		step="$channel"
		channel='Master'
	fi
	amixer set "$channel" "${step}%-" >/dev/null
}
