#!/bin/bash

perform_search() {
	grep -RnI --exclude-dir=.wine --exclude-dir=.svn --exclude-dir=.git "$@"
}

args=()
for arg in "$@"; do
	if [ "$arg" == '-e' ]; then
		open_editor=true
	else
		args+=("$arg")
	fi
done

if [ -n "$open_editor" ]; then
	quickfix=/tmp/search.$$.quickfix
	trap 'rm -f "$quickfix"' EXIT
	perform_search "${args[@]}" | tee "$quickfix"
	[ -s "$quickfix" ] && vim +cw -q "$quickfix"
else
	perform_search --color=auto "${args[@]}"
fi
