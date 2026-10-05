' Dedicated visible UI launch, with no terminal window or restart loop.
Option Explicit
Dim shell, fs, root, python, arguments
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
python = root & "\.venv\Scripts\pythonw.exe"
If Not fs.FileExists(python) Then
    MsgBox "L'environnement Python du projet n'est pas disponible.", vbExclamation, "ZiRcoN Coach"
    WScript.Quit 1
End If
shell.CurrentDirectory = root
arguments = """" & python & """ """ & root & "\run_app.py"" --qml"
shell.Run arguments, 1, False
