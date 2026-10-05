#!/bin/bash
# Editor GM Beauty — diagnóstico da transcrição (Mac/Linux: dois cliques neste arquivo).
cd "$(dirname "$0")/api" || exit 1
[ -x .venv/bin/python ] || { echo 'Abra primeiro o arquivo "iniciar.command" para instalar o editor.'; read -r -p "Enter para fechar..." _; exit 1; }
.venv/bin/python diagnostico.py
echo
read -r -p "Pressione Enter para fechar..." _
