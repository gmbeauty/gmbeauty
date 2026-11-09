@echo off
REM Editor GM Beauty - diagnostico da transcricao (de dois cliques neste arquivo).
cd /d "%~dp0api"
if not exist .venv\Scripts\python.exe (echo Abra primeiro o arquivo "iniciar" para instalar o editor. & pause & exit /b 1)
.venv\Scripts\python diagnostico.py
echo.
pause
