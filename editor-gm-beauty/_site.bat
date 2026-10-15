@echo off
REM Uso interno: liga o site do Editor GM Beauty (aberto pelo "Editor GM Beauty.vbs", sem janela).
cd /d "%~dp0web"
if not exist "%~dp0api\storage\logs" mkdir "%~dp0api\storage\logs"
npm run dev >> "%~dp0api\storage\logs\site.log" 2>&1
