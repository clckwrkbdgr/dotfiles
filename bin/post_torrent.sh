#!/bin/bash
# Creates link to finished torrent and places it to the home directory.
# Also pops up a notification with name of the torrent.
TRANSMISSION_DATA_DIR="$XDG_DATA_HOME/transmission"
mkdir -p "$TRANSMISSION_DATA_DIR"
POST_TR_LOG="$TRANSMISSION_DATA_DIR/post_torrent.sh.log"

[ -z "$TR_TORRENT_DIR" ] && echo "Empty TR_TORRENT_DIR variable" &>>"$POST_TR_LOG" && exit 1
[ -z "$TR_TORRENT_NAME" ] && echo "Empty TR_TORRENT_NAME variable" &>>"$POST_TR_LOG" && exit 1

(
	ln -s "$TR_TORRENT_DIR/$TR_TORRENT_NAME" ~/"$TR_TORRENT_NAME" || (echo "failed to ln -s $TR_TORRENT_DIR/$TR_TORRENT_NAME ~/$TR_TORRENT_NAME"; env);
) &>>"$POST_TR_LOG"

READABLE_NAME=$(echo "$TR_TORRENT_NAME" | sed 's/[.]/ /g')
~/.config/bin/xdg ~/.config/bin/notification -t Transmission "Torrent $READABLE_NAME is finished."
