; Uses CapsLock to switch keyboard layouts on Windows like Linux does.
; Shift+CapsLock can still be used to trigger actual CapsLock functionality.

SetCapsLockState, AlwaysOff
+CapsLock::CapsLock

sel := 0

if (sel=0) {
$capslock::
    send {lwin down}{Space}
    sel := 1
return 
}

$capslock up::
    send {lwin up}
    sel := 0
return 

; Changes hotkeys for switching between virtual desktops
; from default Ctrl+Win+<arrow> to Win+<arrow> like on Linux.
LWin & Right::Send, {LCtrl up}{LWin down}{LCtrl down}{Right}{LWin up}{LCtrl up}
LWin & Left::Send, {LCtrl up}{LWin down}{LCtrl down}{Left}{LWin up}{LCtrl up}

; Local user customizations.

; AutoHotkey cannot do conditional include
; or even recognize arbitrary env. vars in path,
; so we're assuming that %HOME% == %USERPROFILE% == %APPDATA%/../..
; We're also ignoring any errors because AHK cannot detect
; if included script exists or not.
#include *i %A_AppData%\..\..\.local\local.ahk
