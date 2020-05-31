:<<@exit/b
   @%*
@exit/b
   # Prepares user environment for user jobs in crontab.
   # Usage for single command:
   #   ~/.config/bin/crontab-env.cmd <command> <args...>
   # This file can also be sourced from Born-compatible shell:
   #   . ~/.config/bin/crontab-env.cmd; <command> <args...>
   export NO_SCREEN=true # To prevent terminal multiplexor. TODO - need a cross-shell way to detect non-interactive shell.
   . ~/.config/profile
   "$@"
