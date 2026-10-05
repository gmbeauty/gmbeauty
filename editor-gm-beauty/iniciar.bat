@echo off
REM Editor GM Beauty - iniciador para Windows (de dois cliques neste arquivo).
cd /d "%~dp0"

where node >nul 2>nul || (echo FALTA INSTALAR o Node.js: baixe em https://nodejs.org ^(versao LTS^) & pause & exit /b 1)
where python >nul 2>nul || (echo FALTA INSTALAR o Python 3: baixe em https://www.python.org/downloads e marque "Add python.exe to PATH" & pause & exit /b 1)
where ffmpeg >nul 2>nul || (echo FALTA INSTALAR o FFmpeg: abra o Prompt de Comando e rode: winget install ffmpeg & pause & exit /b 1)

REM Chave da OpenAI (opcional): se existir o arquivo chave-openai.txt, a transcricao usa a API da OpenAI.
if exist chave-openai.txt set /p OPENAI_API_KEY=<chave-openai.txt

echo Preparando o servidor (a primeira vez demora alguns minutos)...
if not exist api\.venv python -m venv api\.venv
api\.venv\Scripts\python -m pip install -q -r api\requirements.txt || (echo Erro ao instalar o servidor. Verifique a internet. & pause & exit /b 1)
echo Preparando o site...
if not exist web\node_modules (
  pushd web
  call npm install || (echo Erro ao instalar o site. Verifique a internet. & pause & exit /b 1)
  popd
)

start "Editor GM Beauty - servidor" /D "%~dp0api" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --port 8000"
start "Editor GM Beauty - site" /D "%~dp0web" cmd /k "npm run dev"

echo Aguardando o site iniciar...
timeout /t 10 /nobreak >nul
start http://localhost:3000
echo.
echo Editor GM Beauty rodando em http://localhost:3000
echo Para encerrar, feche as duas janelas "Editor GM Beauty".
pause
