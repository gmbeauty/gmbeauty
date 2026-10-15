#!/bin/bash
# Editor GM Beauty — iniciador para Mac e Linux (no Mac: dê dois cliques neste arquivo).
cd "$(dirname "$0")" || exit 1

falta() { echo; echo "FALTA INSTALAR: $1"; echo "$2"; echo; read -r -p "Pressione Enter para fechar..." _; exit 1; }
command -v node >/dev/null    || falta "Node.js" "Baixe em https://nodejs.org (versão LTS) e rode este arquivo de novo."
command -v python3 >/dev/null || falta "Python 3" "Baixe em https://www.python.org/downloads e rode este arquivo de novo."
command -v ffmpeg >/dev/null  || falta "FFmpeg" "Mac: instale o Homebrew (https://brew.sh) e rode: brew install ffmpeg"

# Chave da OpenAI (opcional): se existir o arquivo chave-openai.txt, a transcrição usa a API da OpenAI.
if [ -f chave-openai.txt ]; then OPENAI_API_KEY="$(tr -d '[:space:]' < chave-openai.txt)"; export OPENAI_API_KEY; fi

echo "Preparando o servidor (a primeira vez demora alguns minutos)..."
[ -d api/.venv ] || python3 -m venv api/.venv || falta "venv do Python" "Reinstale o Python 3."
api/.venv/bin/python -m pip install -q -r api/requirements.txt || falta "dependências do servidor" "Verifique sua internet e tente de novo."
echo "Preparando o site..."
[ -d web/node_modules ] || (cd web && npm install) || falta "dependências do site" "Verifique sua internet e tente de novo."

(cd api && exec .venv/bin/python -m uvicorn app.main:app --port 8000) &
API_PID=$!
(cd web && exec npm run dev) &
WEB_PID=$!
trap 'kill $API_PID $WEB_PID 2>/dev/null; exit 0' INT TERM EXIT

echo "Aguardando o site iniciar..."
for _ in $(seq 1 60); do curl -s -o /dev/null http://localhost:3000 && break; sleep 1; done
if command -v open >/dev/null; then open http://localhost:3000; elif command -v xdg-open >/dev/null; then xdg-open http://localhost:3000; fi

echo
echo "Editor GM Beauty rodando em http://localhost:3000"
echo "Para encerrar, feche esta janela ou pressione Ctrl+C."
wait
