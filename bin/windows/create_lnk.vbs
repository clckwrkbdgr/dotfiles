If WScript.Arguments.Count <> 3 Then
	WScript.Echo "Creates Windows shortcut file." & vbCrLf & "Usage: create_lnk <name.lnk> <target_path> <command line>"
	WScript.Quit
End If

Set shellObject = CreateObject("WScript.Shell")

lnk_name = WScript.Arguments(0)
If InStr(1, lnk_name, "shell:startup") Then
	Const ssfSTARTUP = &H7
	Set shell_app = CreateObject("Shell.Application")
	Set startupFolder = shell_app.NameSpace(ssfSTARTUP)
	lnk_name = Replace(lnk_name, "shell:startup", startupFolder.Self.Path)
End If
target_path = WScript.Arguments(1)
command_line = WScript.Arguments(2)

Set oMyShortCut = shellObject.CreateShortcut(lnk_name)
Const wsMinimized = 7
Const wsMaximized = 0
Const wsNormal = 4
oMyShortCut.WindowStyle = wsNormal ' TODO command line parameter
' oMyShortcut.IconLocation = " TODO path to .ico"
oMyShortCut.TargetPath = target_path
oMyShortCut.Arguments = command_line
oMyShortCut.WorkingDirectory = "c:\" ' TODO command line parameter
oMyShortCut.Save
