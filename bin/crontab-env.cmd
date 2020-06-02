:<<@exit/b
   @echo "crontab-env is deprecated, Use $XDG_CONFIG_HOME/bin/user-env.cmd instead"
   @%*
@exit/b
   # Prepares user environment for user jobs in crontab.
   # Usage for single command:
   #   ~/.config/bin/crontab-env.cmd <command> <args...>
   # This file can also be sourced from Born-compatible shell:
   #   . ~/.config/bin/crontab-env.cmd; <command> <args...>
   export NO_SCREEN=true # To prevent terminal multiplexor. TODO - need a cross-shell way to detect non-interactive shell.
   . ~/.config/profile
   . ~/.config/lib/utils.bash
   deprecated 'Use $XDG_CONFIG_HOME/bin/user-env.cmd instead'
   "$@"
