#!/bin/sh
userstate get metered_network && exit
cd "$XDG_CONFIG_HOME"
git submodule update --init --remote --recursive --merge
git submodule update --recursive # To auto-merge updated submodules with "(new commits)"
