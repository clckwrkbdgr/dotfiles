This dotfiles repo is supposed to be cloned into ~/.config

This is a dotfiles repo that heavily follows [XDG directory specification](http://standards.freedesktop.org/basedir-spec/latest/) and supposed to serve as `XDG_CONFIG_HOME` directory (`~/.config` by default).
All dotfiles from home directory should be stored here, making home dir clear from dotfiles mess.
There are several exceptions, like basic `~/.config`, `~/.local/share`, `~/.cache` from XDG directory spec, or `.profile` and `.bashrc` as they're hardcoded in many out-of-date program and should be left in home root for backward compatibility sake.

All other files are either data (`XDG_DATA_HOME`) or cache (`XDG_CACHE_HOME`) or temp/runtime (`XDG_RUNTIME_DIR`) or user private files. I store latter in `~/.private` dir just to not clutter home dir even more, but this is personal preferences, AFAIK there is no specification for such matters.

For those application that do not support XDG dir spec directly, there are workarounds like command-line switches which allow to store config/data somewhere else, or environmental variables (for same purposes). Such exceptions are handled by `~/.config/bin/xdg` script, which serves as shell source file and a wrapper script both. That is, it could be sourced into the shell instance (like from .bashrc, which my bashrc does), or it could be called to wrap some non-XDG-compliant program into XDG-compliant environment, like `xdg mocp`, for example.

Of course, there are several exceptions that do support neither command-line options nor environment options, notably w3m. For such programs xdg script symlinks theirs .config dirs into old-style home-dir analogues.

Bash prompt is enhanced with script `~/.config/bash/dotfiles_info.bash` which searches for unknown dotfiles and summarizes them in form of hints:
	
	[.2]~$  # There are two unknown dot files.
	[git].config$  # This is a git repo, all dotfiles are for git.

Also `~/.config/bash/dotfiles_info.bash` can be invoked with option `-v` to describe all found dotfiles in current dir.

With all above, there is no 'bootstrap' or 'install' script, dotfiles are working straight from the moment of deploying into `XDG_CONFIG_HOME`, and all exception are handled by `xdg` script, which fixes hardcoded dotfiles in home dir at the first invokation. So, basically, its `git clone ... && . ~/.config/profile`.

Some personal settings (like git config or profile) are stored in `~/.local` dir (e.g. `~/.local/gitconfig`) and included in their respective .config parents, so this setup is customizable and extendable.

## Different dotfiles setups for different systems/devices

Each file in dotfiles repo have attribute `caps` which points to capabilities that corresponding tag is providing. Tags are arbitrary and could represent any kind of capability/platform/OS/features. These attributes can be used to create sparse checkout for specific configuration:

	mkdir .config
	cd .config
	git clone <path to this repo> .
	python caps.py sparse <tag>

Script `update_dotfiles.py` keeps sparse checkout up-to-update with attributes automatically.
