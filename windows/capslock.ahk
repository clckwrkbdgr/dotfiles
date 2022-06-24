; Uses CapsLock to switch keyboard layouts on Windows like Linux does.
; Shift+CapsLock can still be used to trigger actual CapsLock functionality.

SetCapsLockState, AlwaysOff
+CapsLock::CapsLock

; The goal is to have one main (English) language and one secondary (Cyrillic),
; and have an option to switch between secondary languages or keyboard layouts (Russian/Ukrainian).
; As <Win>+<Space> language list displays all languages and layouts alltogether (i.e. all three items),
; we use <LAlt>+<LShift> to switch only between [two]languages,
; and will pick specific layout for he secondary language via <Win>+<Space> manually when needed.
;
; So <LAlt>+<LShift> is required to be enabled and switching method.

$capslock up::
    Send {LAlt down}{LShift}
    send {LAlt up}
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
#include *i %A_AppData%\..\..\.local\share\local.ahk
