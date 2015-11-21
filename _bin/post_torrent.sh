#!/bin/bash

POST_TR_LOG=~/.config/transmission/post_torrent.sh.log

(
	ln -s "$TR_TORRENT_DIR/$TR_TORRENT_NAME" ~/"$TR_TORRENT_NAME" || (echo "failed to ln -s $TR_TORRENT_DIR/$TR_TORRENT_NAME ~/$TR_TORRENT_NAME"; env);
) &>>"$POST_TR_LOG"

aplay -q ~/owlwood/sounds/signal.wav
