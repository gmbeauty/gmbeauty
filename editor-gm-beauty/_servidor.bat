@echo off
REM Uso interno: liga o servidor do Editor GM Beauty (aberto pelo "Editor GM Beauty.vbs", sem janela).
cd /d "%~dp0api"
if exist "%~dp0chave-openai.txt" set /p OPENAI_API_KEY=<"%~dp0chave-openai.txt"
if not exist storage\logs mkdir storage\logs
.venv\Scripts\python -m uvicorn app.main:app --port 8000 >> storage\logs\servidor.log 2>&1
