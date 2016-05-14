#!/bin/bash
# Creates link to finished torrent and places it to the home directory.
# Also pops up a notification with name of the torrent.
TRANSMISSION_DATA_DIR="$XDG_DATA_DIR/transmission"
mkdir -p "$TRANSMISSION_DATA_DIR"
POST_TR_LOG="$TRANSMISSION_DATA_DIR/post_torrent.sh.log"

(
	ln -s "$TR_TORRENT_DIR/$TR_TORRENT_NAME" ~/"$TR_TORRENT_NAME" || (echo "failed to ln -s $TR_TORRENT_DIR/$TR_TORRENT_NAME ~/$TR_TORRENT_NAME"; env);
) &>>"$POST_TR_LOG"

READABLE_NAME=$(echo "$TR_TORRENT_NAME" | sed 's/[.]/ /')
~/.config/bin/xdg ~/.config/bin/johnny alert "Torrent $READABLE_NAME is finished."
