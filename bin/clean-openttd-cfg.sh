#!/bin/sh
if [ "$1" = "--restore" ]; then
	sed 's|$HOME|'"$HOME"'|g'
	exit
fi
sed '/^\[difficulty\]$/,/^\[.*\]$/{//!d}' | \
sed '/^\[game_creation\]$/,/^\[.*\]$/{//!d}' | \
sed 's|'"$HOME"'|$HOME|g'
