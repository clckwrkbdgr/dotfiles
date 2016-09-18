#!/bin/sh
if [ "$1" = "--restore" ]; then
	sed 's|$HOME|'"$HOME"'|g'
	exit
fi
sed '/^default_user_name/d' | \
sed 's|'"$HOME"'|$HOME|g'
