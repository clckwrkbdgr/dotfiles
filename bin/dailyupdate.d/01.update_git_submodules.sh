#!/bin/sh
userstate get metered_network && exit
cd "$XDG_CONFIG_HOME"
git submodule update --init --remote --recursive --merge
if git submodule | grep -q '^+'; then # Having "(new commits)".
	git stash --keep-index
	git submodule -q foreach 'echo $sm_path' | xargs git add
	git commit -m 'Updated submodules.'
	git stash pop
fi
