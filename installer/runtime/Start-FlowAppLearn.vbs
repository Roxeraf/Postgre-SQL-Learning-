Option Explicit
Dim sh, fso, root, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("Wscript.Shell")
sh.CurrentDirectory = root
cmd = "powershell.exe -STA -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & root & "\Start-FlowAppLearn.ps1"""
sh.Run cmd, 0, False
