#!/bin/sh
userstate get metered_network && exit
git submodule update --init --remote --recursive --merge
