#!/bin/sh

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi
if [ -d "$HOME/.config/bin" ] ; then
    PATH="$HOME/.config/bin:$PATH"
fi
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
if [ -d "$HOME/.projects/bin" ] ; then
    PATH="$HOME/.projects/bin:$PATH"
fi
if [ -d "$HOME/.private/bin" ] ; then
    PATH="$HOME/.private/bin:$PATH"
fi
