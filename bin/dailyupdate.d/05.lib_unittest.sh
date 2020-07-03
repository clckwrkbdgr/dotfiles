#!/bin/sh
cd "$XDG_CONFIG_HOME/lib"
quiet=-q
[ -n "$DAILYUPDATE_VERBOSE" ] && quiet=
unittest $quiet
