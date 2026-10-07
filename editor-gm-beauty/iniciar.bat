@echo off
REM Editor GM Beauty - iniciador para Windows (de dois cliques neste arquivo).
cd /d "%~dp0"

where node >nul 2>nul || (echo FALTA INSTALAR o Node.js: baixe em https://nodejs.org ^(versao LTS^), instale, FECHE esta janela e abra este arquivo de novo. & pause & exit /b 1)
where ffmpeg >nul 2>nul || (echo FALTA INSTALAR o FFmpeg: abra o Prompt de Comando e rode: winget install ffmpeg . Depois FECHE esta janela e abra este arquivo de novo. & pause & exit /b 1)

REM Procura um Python que realmente funcione (o "python" da Microsoft Store e um atalho falso).
set "PY="
py -3 -c "import sys" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys" >nul 2>nul && set "PY=python"
if not defined PY (
  echo FALTA INSTALAR o Python: baixe a versao 3.12 em https://www.python.org/downloads/windows/
  echo Na instalacao, marque "Add python.exe to PATH". Depois FECHE esta janela e abra este arquivo de novo.
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info[:2] <= (3,13) else 1)" >nul 2>nul || (
  echo AVISO: seu Python e muito novo e alguns componentes do editor podem nao instalar.
  echo Se der erro, instale o Python 3.12 em https://www.python.org/downloads/windows/ e tente de novo.
  echo.
)

REM Chave da OpenAI (opcional): se existir o arquivo chave-openai.txt, a transcricao usa a API da OpenAI.
if exist chave-openai.txt set /p OPENAI_API_KEY=<chave-openai.txt

echo Preparando o servidor (a primeira vez demora alguns minutos)...
if not exist api\.venv %PY% -m venv api\.venv
api\.venv\Scripts\python -m pip install -q -r api\requirements.txt || (echo Erro ao instalar o servidor. Verifique a internet e tente de novo. Se o erro falar de "Microsoft Visual C++", instale: https://aka.ms/vs/17/release/vc_redist.x64.exe & pause & exit /b 1)
echo Preparando o site...
if not exist web\node_modules (
  pushd web
  call npm install || (echo Erro ao instalar o site. Verifique a internet e tente de novo. & pause & exit /b 1)
  popd
)

start "Editor GM Beauty - servidor" /D "%~dp0api" cmd /k ".venv\Scripts\python -m uvicorn app.main:app --port 8000"
start "Editor GM Beauty - site" /D "%~dp0web" cmd /k "npm run dev"

echo Aguardando o site iniciar...
timeout /t 12 /nobreak >nul
start http://localhost:3000
echo.
echo Editor GM Beauty rodando em http://localhost:3000
echo Se o Windows perguntar sobre o Firewall, clique em "Permitir acesso" (rede privada).
echo Para encerrar, feche as duas janelas "Editor GM Beauty".
pause
