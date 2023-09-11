:<<@exit/b
   @ECHO OFF
   REM Init script for Windows CMD
   REM Depends on Python (see below).
   REM To install:
   REM   reg add "HKCU\Software\Microsoft\Command Processor" /v AutoRun /t REG_EXPAND_SZ /d "%"USERPROFILE"%\.config\bin\user-env.cmd" /f

   REM MS Idiots think that User PATH should go _after_ System PATH.
   REM While actual users need otherwise
   REM We also cannot use 'normal' parsing functionality that comes with CMD (FOR ...), because it results in recursion somehow.

   REM First we check if user path is already prepended: it should be present twice, one for already _appended_ by the idiot MS, and one "fixed" by us.
   ECHO "%PATH%" | FINDSTR /R "\\.config\\bin\\windows.*\\.config\\bin\\windows" >NUL
   IF ERRORLEVEL 1 GOTO NO_USER_PATH_YET
   GOTO USERPATH_IS_ALREADY_SET
   REM This hack with GOTO is used because if we try to SET varible inside IF ( ) block, it will be expanded (to empty string, ofc) before script is executed at all.
   :NO_USER_PATH_YET
      REM And we use Python, because there is no valid and proper option in plain CMD to catch output from a command and store it in a variable.
      REG QUERY HKCU\Environment /V Path | FINDSTR REG_EXPAND_SZ 2>NUL | python.exe -c "import os, sys; filename=os.environ['TEMP'] + '\\userpath.bat'; f = open(filename, 'w'); f.write('@ECHO OFF\nSET \x22USER_PATH='); f.write(sys.stdin.read().split(None, 2)[-1].rstrip()); f.write('\x22')" 2>NUL
      call %TEMP%\userpath.bat
      SET "PATH=%USER_PATH%;%PATH%"
   :USERPATH_IS_ALREADY_SET

   REM Loading generic doskey aliases (if present).
   IF EXIST %USERPROFILE%\.config\alias.doskey (
      doskey /macrofile=%USERPROFILE%\.config\windows\alias.doskey
   )

   REM Loading custom doskey aliases (if present).
   IF EXIST %USERPROFILE%\.local\alias.doskey (
      doskey /macrofile=%USERPROFILE%\.local\alias.doskey
   )
   IF EXIST %USERPROFILE%\.local\share\alias.doskey (
      doskey /macrofile=%USERPROFILE%\.local\share\alias.doskey
   )

   REM Now we can run application in created environment.
   REM This is done primarily for Far Manager because it cannot hold environment from AutoRun cmd file,
   REM each new command line will fall back to the initial environment.
   IF NOT [%1] == [] call %*
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
   exec "$@"
