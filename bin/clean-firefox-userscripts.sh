#!/bin/sh
if [ "$1" = "--restore" ]; then
	sed 's|$HOME|'"$HOME"'|g'
	exit
fi
sed 's/installTime="[0-9]\+"/installTime="0"/' | \
sed 's/modified="[0-9]\+"/modified="0"/' | \
sed 's|'"$HOME"'|$HOME|g'
