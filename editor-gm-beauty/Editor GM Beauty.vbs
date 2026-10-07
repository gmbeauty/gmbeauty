' Editor GM Beauty - abre o editor SEM janelas pretas (de dois cliques neste arquivo).
Option Explicit

Dim sh, fso, base, i
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)

If Not fso.FileExists(base & "\iniciar.bat") Then
  MsgBox "Este arquivo precisa ficar DENTRO da pasta do editor (a pasta 'editor-gm-beauty')," & vbCrLf & _
         "junto dos arquivos 'iniciar', 'api' e 'web'." & vbCrLf & vbCrLf & _
         "Copie este arquivo para la e abra de novo.", 48, "Editor GM Beauty"
  WScript.Quit
End If

' Primeira vez: usa o instalador com janela, para mostrar o progresso e eventuais erros.
If Not fso.FolderExists(base & "\api\.venv") Or Not fso.FolderExists(base & "\web\node_modules") Then
  MsgBox "Primeira vez: vou instalar o que falta (alguns minutos, precisa de internet)." & vbCrLf & _
         "Uma janela preta vai abrir. Nao feche ate o navegador abrir.", 64, "Editor GM Beauty"
  sh.Run """" & base & "\iniciar.bat""", 1, False
  WScript.Quit
End If

' Ja esta rodando? Entao so abre o navegador.
If Up("http://localhost:8000/health") And Up("http://localhost:3000") Then
  sh.Run "http://localhost:3000"
  WScript.Quit
End If

EnsureFolder base & "\api\storage"
EnsureFolder base & "\api\storage\logs"

' Liga o servidor e o site escondidos (sem janelas).
If Not Up("http://localhost:8000/health") Then sh.Run """" & base & "\_servidor.bat""", 0, False
If Not Up("http://localhost:3000") Then sh.Run """" & base & "\_site.bat""", 0, False

' Espera ficar pronto (ate uns 3 minutos) e abre o navegador.
For i = 1 To 90
  If Up("http://localhost:8000/health") And Up("http://localhost:3000") Then
    sh.Run "http://localhost:3000"
    WScript.Quit
  End If
  WScript.Sleep 1500
Next

MsgBox "Nao consegui iniciar o editor." & vbCrLf & vbCrLf & _
       "Vou abrir a pasta com o registro. Se precisar de ajuda, tire um print do arquivo mais recente" & vbCrLf & _
       "ou abra o arquivo 'diagnostico' desta pasta.", 48, "Editor GM Beauty"
sh.Run "explorer """ & base & "\api\storage\logs""", 1, False

Sub EnsureFolder(p)
  If Not fso.FolderExists(p) Then fso.CreateFolder p
End Sub

Function Up(url)
  Dim h
  Up = False
  On Error Resume Next
  Set h = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  h.setTimeouts 2000, 2000, 5000, 30000
  h.Open "GET", url, False
  h.Send
  If Err.Number = 0 Then
    If h.Status = 200 Then Up = True
  End If
  Err.Clear
  On Error GoTo 0
End Function
