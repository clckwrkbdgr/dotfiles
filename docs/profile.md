# Shell profile loading sequence

	workstation boots     remote connection (ssh)
	            |            |
	            |            |
	          login shell opens
	          [L] login profile is read
	          login prompt displays...
	               |      |
				   |     X session is opened
				   |                    |
		subshell is opened              |
		(e.g. from within program)  terminal emulator
				   |                is opened
				   |                   |               ...
	       interactive non-login shell opens            |
	       [I] non-login profile is sourced       arbitrary process
				           |                        |
	                 shell script or command is executed
					 non-interactive non-login shell opens
					 [N] non-interactive environment is set

**NOTE:** Every subprocess inherits it's parent environment (environment variables), but not shell setup (e.g. functions, aliases, not exported variables etc).

## [L] Login shell

**Login shell** (whether interactive or not) is a shell opened for logging user in, either physically via local terminal, or remotely e.g. via ssh. This shell starts for user session and sources set of files _once_. It should prepare full environment that will be propagated to all subprocesses. GUI sessions usually also start non-interactive login shell which perform login via DM (e.g. `xdm`), thus the environment prepared with `*profile` is inherited by any application started using desktop icons, menus, DM keybindings or any other GUI way.

No executable program (mail check, greetings etc) is expected here (even for interactive login shells). Use non-login source files for that purpose. The only exception is session-related programs that should be called only once: `ssh-agent`, `screen`/`tmux` etc.

Processing chain for shells:

|=     sh       =|=         bash        =|=       zsh       =|=       ksh       =|=  csh, tcsh   =|
|----------------|-----------------------|-------------------|-------------------|----------------|
| `/etc/profile` | `/etc/profile`        | `/etc/profile`    | `/etc/profile`    | `/etc/profile` |
|                | `~/.bash_profile` (1) | `~/.zprofile` (?) | (?)               | `~/.login`     |
|                | `~/.bash_login`   (1) |       (?)         |      (?)          | (?)            |
| `~/.profile`   | `~/.profile`      (1) |       (?)         | `~/.profile`      | (?)            |

**(1)** - only the first existing file of the following is read.

- `/etc/profile` - system environment/shell profile (assumed to be Born shell compatible).
- `~/.bash_profile` - bash-only analogue of `~/.profile`.
- `~/.bash_login` - synonym for `.bash_profile`.
- `~/.zprofile` - zsh-only analogue of `~/.profile`.
- `~/.profile` - generic profile for different shells (assumed to be Born shell compatible).

Login profiles do not load `~/.bashrc`, it must be done manualy if needed (for interactive login shell), e.g. at the end of `~/.bash_profile` or `~/.profile`. In the latter case, additional test is needed to ensure that current shell is in fact bash.

However, for original Born shell (`/bin/sh`) and Korn shell (`ksh`) environment variable `$ENV` is automatically read, expanded and sourced for interactive shell even if it is login shell.

## [I] Interactive non-login shell

**Non-login shell** (interactive only) is a shell started explicitly by user within its user session. E.g. opening subshell from command line, or starting interactive shell from subprocess (`:sh` in Vim).

Such shells re-execute startup file sequences for each new (sub)process. E.g. if some existing enviroment variables get expanded, they will be for each level of subshell, which may result in needless duplication. Settings like these are better to be placed to `.profile`.

Shell configuration related to user interaction is done here: aliases, functions, prompt, shell options etc.

Processing chain for shells:

|=  sh  =|=    bash          =|=     zsh  =|=   ksh    =|= csh, tcsh =|
|--------|--------------------|------------|------------|-------------|
|        | `/etc/bash.bashrc` | (?)        | (?)        | (?)         |
| `$ENV` | `~/.bashrc`        | `~/.zshrc` | `~/.kshrc` | `~/.cshrc`  |

Non-login shells do not (neither they should to) read/execute login shell profiles, as profile is a set of instructions that should be executed only once for a user session. If some part of profile needs to be re-run for every instance of interactive subshell, it should be extracted to a separate file and that file should be sourced in `~/.bashrc`.

## [N] Non-interactive shell

**Non-interactive shell** (non-login only) is shell process started to execute a shell script or a shell command.

Processing for **bash**:

1. If `$BASH_ENV` exists in the environment, it gets shell-expanded and treated as shell file, which is sourced for every new non-interactive non-login shell process.

Non-interactive shells do not reread any profile/shell configuration files. Non-interactive shell process works with default environment it inherits from the parent. All shell-specific stuff (aliases, not exported functions etc) are _not inherited_ as such and should be sourced manually within the script if needed.
