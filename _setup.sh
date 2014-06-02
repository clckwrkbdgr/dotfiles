#!/bin/bash

DOTDIR=~/dotfiles
DOTDIR_CONFIG=~/dotfiles/_config
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

mkdir -p "$BACKUP_DOTDIR/.config"
pushd "$DOTDIR_CONFIG" >/dev/null
for FILE in *; do
	DEST="$HOMEDIR/.config/$FILE"
	if [ -e "$DEST" ]; then
		mv --backup=t "$DEST" "$BACKUP_DOTDIR/.config" && ln -s "${DOTDIR_CONFIG}/${FILE}" "$DEST" || echo "Error during copying .$FILE"
	else
		ln -s "${DOTDIR_CONFIG}/${FILE}" "$DEST" || echo "Error during copying .$FILE"
	fi
done
popd >/dev/null
