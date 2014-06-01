#!/bin/bash

DOTDIR=~/dotfiles
BACKUP_DOTDIR=~/dotfiles.bak
HOMEDIR=~

mkdir -p "$BACKUP_DOTDIR"
for FILE in [^_]*; do
	mv -b "$HOMEDIR/.$FILE" "$BACKUP_DOTDIR"
	ln -s "${DOTDIR}/${FILE}" "$HOMEDIR/.$FILE"
done
