#!/bin/sh
if [ "$1" = "--restore" ]; then
	XRESOLUTION=$(xrandr |grep \* |awk '{print $1}' | sed 's/x/,/')
	sed 's|$HOME|'"$HOME"'|g'
	sed 's|$XRESOLUTION|'"$XRESOLUTION"'|g'
	exit
fi
sed '/^\[difficulty\]$/,/^\[.*\]$/{//!d}' | \
sed '/^\[game_creation\]$/,/^\[.*\]$/{//!d}' | \
sed '/^station_numtracks *=/d' | \
sed '/^station_platlength *=/d' | \
sed '/^transparency_options *=/d' | \
sed 's/^resolution *=.*/resolution = $XRESOLUTION/' | \
sed 's|'"$HOME"'|$HOME|g'
