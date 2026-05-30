' Hidden-window launcher for daily_predict.ps1.
'
' Windows Task Scheduler with `powershell.exe -WindowStyle Hidden -File ...`
' still flashes a console window on launch because Hidden is applied after the
' console is created. wscript.exe + Shell.Run with intWindowStyle=0 truly
' suppresses the console, eliminating the flash on laptop wake.
'
' Waits for PowerShell to exit (bWaitOnReturn=True) and exits with the same
' code, so Task Scheduler's LastTaskResult still reflects real success/failure.

Option Explicit
Dim shell, repo, exitCode
repo = "C:\Users\kesav\OneDrive\Desktop\code\trade"
Set shell = CreateObject("WScript.Shell")
exitCode = shell.Run("powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & repo & "\scripts\daily_predict.ps1""", 0, True)
WScript.Quit exitCode
