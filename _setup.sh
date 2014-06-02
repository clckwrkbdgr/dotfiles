#!/bin/bash

DOTDIR=~/dotfiles
BACKUP_DOTDIR=~/dotfiles.bak
HOMEDIR=~

mkdir -p "$BACKUP_DOTDIR"
for FILE in [^_]*; do
	DEST="$HOMEDIR/.$FILE"
	if [ -e "$DEST" ]; then
		mv --backup=t "$DEST" "$BACKUP_DOTDIR" && ln -s "${DOTDIR}/${FILE}" "$DEST" || echo "Error during copying .$FILE"
	else
		ln -s "${DOTDIR}/${FILE}" "$DEST" || echo "Error during copying .$FILE"
	fi
done
