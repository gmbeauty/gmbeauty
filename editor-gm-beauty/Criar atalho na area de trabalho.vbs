' Editor GM Beauty - cria os atalhos na area de trabalho (de dois cliques, so precisa fazer uma vez).
Option Explicit

Dim sh, fso, base, desk
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
desk = sh.SpecialFolders("Desktop")

If Not fso.FileExists(base & "\iniciar.bat") Then
  MsgBox "Este arquivo precisa ficar DENTRO da pasta do editor (a pasta 'editor-gm-beauty')," & vbCrLf & _
         "junto dos arquivos 'iniciar', 'api' e 'web'." & vbCrLf & vbCrLf & _
         "Copie este arquivo para la e abra de novo.", 48, "Editor GM Beauty"
  WScript.Quit
End If

MakeLink desk & "\Editor GM Beauty.lnk", base & "\Editor GM Beauty.vbs", "Abrir o Editor GM Beauty"
MakeLink desk & "\Parar Editor GM Beauty.lnk", base & "\Parar Editor GM Beauty.vbs", "Encerrar o Editor GM Beauty"

MsgBox "Pronto! Dois atalhos foram criados na area de trabalho:" & vbCrLf & vbCrLf & _
       "- Editor GM Beauty (abre o editor)" & vbCrLf & _
       "- Parar Editor GM Beauty (encerra o editor)", 64, "Editor GM Beauty"

Sub MakeLink(path, script, desc)
  Dim l
  Set l = sh.CreateShortcut(path)
  l.TargetPath = "wscript.exe"
  l.Arguments = """" & script & """"
  l.WorkingDirectory = base
  l.IconLocation = base & "\icone.ico"
  l.Description = desc
  l.Save
End Sub
