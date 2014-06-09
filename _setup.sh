#!/bin/bash

DOTDIR=~/dotfiles
DOTDIR_CONFIG=~/dotfiles/_config
DOTDIR_BIN=~/dotfiles/_bin
BACKUP_DOTDIR=~/dotfiles.bak
HOMEDIR=~

get_abs_filename() {
	REL_FILENAME=$1
	echo "$(cd "$(dirname "$REL_FILENAME")" && pwd)/$(basename "$REL_FILENAME")"
}

function setup_files_from_dir()
{
	DIR_NAME=$1
	ACTUAL_DIR_NAME=$2

	BACKUP_DIR_NAME=$(get_abs_filename "${BACKUP_DOTDIR}/${ACTUAL_DIR_NAME}")
	DOTDIR_NAME=$(get_abs_filename "${DOTDIR}/${DIR_NAME}")
	DEST_DIR_NAME=$(get_abs_filename "${HOMEDIR}/${ACTUAL_DIR_NAME}/")

	echo "Installing <$DIR_NAME> to <$DEST_DIR_NAME>."
	mkdir -p "$BACKUP_DIR_NAME"
	pushd "$DOTDIR_NAME" >/dev/null
	for FILE in [^_]*; do
		DEST="${DEST_DIR_NAME}/${FILE}"
		[ "$DIR_NAME" == '.' ] && DEST="${DEST_DIR_NAME}/.${FILE}"
		DEST=$(get_abs_filename "$DEST")
		DOTFILE_NAME=$(get_abs_filename "${DOTDIR_NAME}/${FILE}")

		echo -e "\t$FILE"
		if [ -e "$DEST" -o -h "$DEST" ]; then
			mv --backup=t "$DEST" "$BACKUP_DIR_NAME" && ln -s "$DOTFILE_NAME" "$DEST" || echo "Error during copying '$FILE'"
		else
			ln -s "$DOTFILE_NAME" "$DEST" || echo "Error during copying .$FILE"
		fi
	done
	popd >/dev/null
}

setup_files_from_dir . .
setup_files_from_dir _config .config
setup_files_from_dir _bin bin
