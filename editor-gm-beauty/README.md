# Editor GM Beauty

Transforme vídeos brutos em conteúdo pronto para postar.

Fluxo: **upload → escolher tipo e estilo → edição automática → revisar → exportar** (MP4 H.264, 1080×1920, 9:16).

## O que já funciona (Fases 1–8)

- Dashboard com projetos (miniatura, status, duplicar, excluir permanente).
- Upload de MP4/MOV com barra de progresso.
- Transcrição em português com timestamps por palavra (Whisper).
- Detecção de pausas e remoção opcional (só o miolo das pausas longas; a fala continua natural).
- Legendas: tradicional, com palavras destacadas e palavra por palavra; cores GM; contorno e sombra leves; zona segura de Reels/TikTok.
- Correção de qualquer legenda (texto e tempos) antes de exportar.
- Estilos GM Clean, GM Viral, GM Produto e GM Oferta.
- Logo opcional (posição, tamanho e transparência).
- Exportação 9:16 e download.

## O que você precisa instalar

1. **Node 20+** (https://nodejs.org)
2. **Python 3.10+**
3. **FFmpeg** (com libx264): `brew install ffmpeg` (Mac) · `sudo apt install ffmpeg` (Linux) · `winget install ffmpeg` (Windows)

## Como executar

Abra dois terminais.

**Terminal 1 — servidor (API)**
```bash
cd editor-gm-beauty/api
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://localhost:8000
```

**Terminal 2 — site**
```bash
cd editor-gm-beauty/web
npm install
npm run dev                      # abra http://localhost:3000
```

### Transcrição (escolha uma)

- **Local e gratuita (padrão sem chave):** nada a configurar. Na 1ª vez baixa o modelo Whisper (~500 MB para `small`) e transcreve no seu computador. Para mais precisão: `WHISPER_MODEL=medium`.
- **API da OpenAI (mais rápida):** `export OPENAI_API_KEY=sua-chave` antes de iniciar o servidor.

Variáveis opcionais do servidor: `CAPTION_FONT` (fonte das legendas no vídeo; precisa estar instalada, padrão `Arial`), `CAPTION_FONTS_DIR` (pasta com fontes extras), `DATA_DIR` (onde ficam os vídeos), `DATABASE_URL` (PostgreSQL/Supabase), `MAX_UPLOAD_MB`.

## Testes

```bash
cd api && source .venv/bin/activate && python -m pytest -q   # usa FFmpeg com vídeo de verdade
cd web && npm run lint && npm run build
```

## Limitações conhecidas

- **Whisper real não foi testado no ambiente de desenvolvimento** (sem acesso ao download do modelo). Os testes usam uma transcrição simulada; os caminhos `local` e `openai` precisam do seu primeiro teste real. Se algo falhar, a tela mostra uma mensagem simples e o detalhe técnico fica em `api/storage/logs/app.log`.
- **Prévia de vídeos HEVC (alguns .mov de iPhone):** o upload e a exportação funcionam, mas alguns navegadores não tocam a prévia.
- **Sem login:** o app assume um único usuário rodando no próprio computador. Antes de colocar online é obrigatório adicionar login (ver `ARCHITECTURE.md`).
- Valores da zona segura são aproximados; ajuste em `web/src/lib/safe-zone.ts` e `api/app/services/ass.py` (mantenha os dois iguais).
- Fonte das legendas é definida no servidor; ainda não há escolha de fonte na tela.

Veja `ARCHITECTURE.md` para as decisões técnicas.
