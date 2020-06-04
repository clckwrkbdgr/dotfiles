:<<@exit/b
   @%*
@exit/b
   # Prepares full user environment, e.g. for user jobs in crontab.
   # Re-read user profile each time, so can be used to run command
   # in up-to-date environment without restart of underlying service,
   # e.g. DE keybindings.
   # Usage for single command:
   #   ~/.config/bin/user-env.cmd <command> <args...>
   # This file can also be sourced from Born-compatible shell:
   #   . ~/.config/bin/user-env.cmd; <command> <args...>
   export NO_SCREEN=true # To prevent terminal multiplexor. TODO - need a cross-shell way to detect non-interactive shell.
   . ~/.config/profile
   "$@"
