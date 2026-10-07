' Editor GM Beauty - encerra o editor (de dois cliques neste arquivo).
Option Explicit

Dim sh
Set sh = CreateObject("WScript.Shell")

' Encerra quem esta escutando nas portas do editor (8000 = servidor, 3000 = site).
sh.Run "powershell -NoProfile -WindowStyle Hidden -Command ""Get-NetTCPConnection -LocalPort 8000,3000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }""", 0, True

MsgBox "Editor GM Beauty encerrado.", 64, "Editor GM Beauty"
