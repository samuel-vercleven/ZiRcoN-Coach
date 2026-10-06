' Normal application entry point, without a terminal or restart loop.
Option Explicit
Dim shell, fs, root, python
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
python = root & "\.venv\Scripts\pythonw.exe"
If Not fs.FileExists(python) Then
    MsgBox "L'environnement Python du projet n'est pas disponible.", vbExclamation, "ZiRcoN Coach"
    WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run """" & python & """ """ & root & "\run_app.py""", 1, False
