#!/bin/bash

get_abs_filename() {
	REL_FILENAME=$1
	echo "$(cd "$(dirname "$REL_FILENAME")" && pwd)/$(basename "$REL_FILENAME")"
}

function setup_files_from_dir()
{
	SRC_DIR=$1
	DIR_NAME=$2
	DEST_DIR=$3
	ACTUAL_DIR_NAME=$4
	BACKUP_DOTDIR="${SRC_DIR}.bak"

	mkdir -p "${BACKUP_DOTDIR}/${ACTUAL_DIR_NAME}"
	BACKUP_DIR_NAME=$(get_abs_filename "${BACKUP_DOTDIR}/${ACTUAL_DIR_NAME}")
	DOTDIR_NAME=$(get_abs_filename "${SRC_DIR}/${DIR_NAME}")
	DEST_DIR_NAME=$(get_abs_filename "${DEST_DIR}/${ACTUAL_DIR_NAME}/")

	echo "Installing <$DIR_NAME> to <$DEST_DIR_NAME>."
	pushd "$DOTDIR_NAME" >/dev/null
	for FILE in [^_]*; do
		mkdir -p "${DEST_DIR_NAME}"
		DEST="${DEST_DIR_NAME}/${FILE}"
		[ "$DIR_NAME" == '.' ] && DEST="${DEST_DIR_NAME}/.${FILE}"
		DEST=$(get_abs_filename "$DEST")
		DOTFILE_NAME=$(get_abs_filename "${DOTDIR_NAME}/${FILE}")

		echo -e "\t$FILE"
		if [ -e "$DEST" -o -h "$DEST" ]; then
			mv --backup=t "$DEST" "$BACKUP_DIR_NAME" && ln -s "$DOTFILE_NAME" "$DEST" || echo "Error during copying '$FILE'"
		else
			ln -s "$DOTFILE_NAME" "$DEST" || echo "Error during copying $FILE to $DEST"
		fi
	done
	popd >/dev/null
}

function panic() {
	echo 'Failed:' $1;
	exit 1
}

function test_setup_files_from_dir()
{
	HOSTDIR="$(mktemp -d)"
	mkdir $HOSTDIR/dotfiles
	echo 'value' > $HOSTDIR/dotfiles/dotfile
	echo 'old_value' > $HOSTDIR/.existing_dotfile
	echo 'new_value' > $HOSTDIR/dotfiles/existing_dotfile
	echo 'existing_link' > $HOSTDIR/dotfiles/existing_link
	ln -s $HOSTDIR/dotfiles/existing_link $HOSTDIR/.existing_link
	mkdir $HOSTDIR/dotfiles/_config
	echo 'config_value' > $HOSTDIR/dotfiles/_config/dotfile

	setup_files_from_dir $HOSTDIR/dotfiles . $HOSTDIR .
	setup_files_from_dir $HOSTDIR/dotfiles _config $HOSTDIR .config

	[ -d $HOSTDIR/dotfiles ] || panic "dotfiles dir is missing!"
	[ -f $HOSTDIR/dotfiles/dotfile ] || panic "original dotfiles are missing!"
	[ -f $HOSTDIR/dotfiles/existing_dotfile ] || panic "original dotfiles are missing!"
	[ -f $HOSTDIR/dotfiles/existing_link ] || panic "original dotfiles are missing!"
	[ -d $HOSTDIR/dotfiles/_config ] || panic "config dotfiles dir is missing!"
	[ -f $HOSTDIR/dotfiles/_config/dotfile ] || panic "original config dotfiles are missing!"

	[ -d $HOSTDIR/dotfiles.bak ] || panic "dotfiles backup dir is missing!"
	[ -h $HOSTDIR/.dotfile ] || panic ".dotfile is missing!"
	[ "x$(readlink $HOSTDIR/.dotfile)" == "x$HOSTDIR/dotfiles/dotfile" ] || panic ".dotfile is incorrect!"

	[ -h $HOSTDIR/.existing_dotfile ] || panic ".existing_dotfile is missing!"
	[ "x$(readlink $HOSTDIR/.existing_dotfile)" == "x$HOSTDIR/dotfiles/existing_dotfile" ] || panic ".existing_dotfile is incorrect!"
	[ -f $HOSTDIR/dotfiles.bak/.existing_dotfile ] || panic ".existing_dotfile backup is missing!"
	[ "x$(cat $HOSTDIR/.existing_dotfile)" == "xnew_value" ] || panic ".existing_dotfile is incorrect!"
	[ "x$(cat $HOSTDIR/dotfiles.bak/.existing_dotfile)" == "xold_value" ] || panic ".existing_dotfile backup is incorrect!"

	[ -h $HOSTDIR/.existing_link ] || panic ".existing_link is missing!"
	[ "x$(readlink $HOSTDIR/.existing_link)" == "x$HOSTDIR/dotfiles/existing_link" ] || panic ".existing_link is incorrect!"
	[ -h $HOSTDIR/dotfiles.bak/.existing_link ] || panic ".existing_link backup is missing!"
	[ "x$(readlink $HOSTDIR/dotfiles.bak/.existing_link)" == "x$HOSTDIR/dotfiles/existing_link" ] || panic ".existing_link backup is incorrect!"

	[ -d $HOSTDIR/.config ] || panic ".config dir is missing!"
	[ -h $HOSTDIR/.config/dotfile ] || panic ".config/dotfile is missing!"
	[ "x$(readlink $HOSTDIR/.config/dotfile)" == "x$HOSTDIR/dotfiles/_config/dotfile" ] || panic ".config/dotfile is incorrect!"
	echo 'Done. Ok.'
}

if [ "x$1" == "xtest" ]; then
	test_setup_files_from_dir
	exit $?
fi

DOTDIR=~/dotfiles
HOMEDIR=~
setup_files_from_dir $DOTDIR . $HOMEDIR .
setup_files_from_dir $DOTDIR _config $HOMEDIR .config
setup_files_from_dir $DOTDIR _bin $HOMEDIR bin
