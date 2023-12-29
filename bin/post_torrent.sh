#!/bin/bash
# Performs post actions for downloaded torrent.
# <https://github.com/transmission/transmission/wiki/Scripts#On_Torrent_Completion>
# If "$XDG_CONFIG_HOME/local/transmission/post_torrent.sh" is present, tries to execute it (all Transmission-defined environment variables should be available).
# Otherwise legacy location "$XDG_DATA_HOME/transmission/post_torrent.sh" is checked.
# Otherwise by default pops up a notification with name of the torrent.
. "$XDG_CONFIG_HOME/lib/utils.bash"

[ -z "$TR_TORRENT_DIR" ] && panic "Empty TR_TORRENT_DIR variable"
[ -z "$TR_TORRENT_NAME" ] && panic "Empty TR_TORRENT_NAME variable"

TRANSMISSION_STATE_DIR="$XDG_STATE_HOME/transmission"
mkdir -p "$TRANSMISSION_STATE_DIR"
exec >>"$TRANSMISSION_STATE_DIR/post_torrent.sh.log"
exec 2>&1

if [ -x "$XDG_CONFIG_HOME/local/transmission/post_torrent.sh" ]; then
	"$XDG_CONFIG_HOME/local/transmission/post_torrent.sh"
elif [ -x "$XDG_DATA_HOME/transmission/post_torrent.sh" ]; then
	"$XDG_DATA_HOME/transmission/post_torrent.sh"
else
	notification -t Transmission "Torrent $TR_TORRENT_NAME is finished."
fi
