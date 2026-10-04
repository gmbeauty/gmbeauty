# Arquitetura — Editor GM Beauty

## Visão geral

```
Navegador (Next.js)  ──HTTP──▶  API (FastAPI)  ──▶  FFmpeg / Whisper
                                    │
                                    ├──▶ Banco (PostgreSQL / Supabase)
                                    └──▶ Arquivos privados (Supabase Storage / R2)
```

- **web/**: telas e interação (dashboard, upload, editor). Não processa vídeo.
- **api/**: recebe vídeos, roda o pipeline, entrega o resultado.
- Todas as chamadas do frontend passam por `web/src/lib/api.ts`. Ela fala com a API (FastAPI) e traduz erros técnicos em mensagens simples.

## Pipeline (implementado)

Upload → extrair áudio → transcrever (timestamps por palavra) → detectar silêncios → sugerir cortes → montar legendas → aplicar preset → renderizar → MP4 1080×1920 H.264.
Cada etapa é uma função em `api/app/services/`, para testar e trocar uma sem mexer nas outras.

## Estrutura de pastas

```
editor-gm-beauty/
├── ARCHITECTURE.md, README.md
├── web/src/
│   ├── app/            páginas: / , /novo , /editor/[id]
│   ├── components/     peças visuais; components/editor/ = tela do editor
│   └── lib/            tipos, presets, tipos de conteúdo, safe zone, api
└── api/app/
    ├── main.py         entrada da API
    ├── routers/        rotas HTTP
    └── services/       ffmpeg, transcrição, legendas, silêncios
```

## Banco de dados

SQLite local por padrão (`DATABASE_URL` troca para PostgreSQL/Supabase sem mudar o código).

- `projects`: id, **owner_id** (hoje sempre "local"), nome, status (draft/processing/ready/error), etapa e progresso, tipo de conteúdo, estilo, dados do vídeo, `settings` (JSON), `captions` (JSON), `silences` (JSON), mensagem de erro para a pessoa e **detalhe técnico separado**.
- `dictionary_terms`: Dicionário GM Beauty (marcas e produtos). Já é enviado ao Whisper como dica de vocabulário; falta só a tela de cadastro.
- Legendas e silêncios ficam em JSON dentro do projeto (sempre lidos/gravados juntos); se um dia precisarmos consultar por palavra, viram tabelas próprias.

## Privacidade e exclusão

Arquivos ficam em armazenamento **privado** (nunca URL pública; acesso por link temporário assinado). Excluir um projeto apaga o registro e todos os arquivos (original, áudio, exportado).

## Erros

O usuário vê mensagens simples ("Não conseguimos processar este vídeo. Tente novamente."). O detalhe técnico (saída do FFmpeg etc.) é gravado em log/campo interno do projeto, nunca na tela.

## Decisões (e o que ainda pode mudar)

1. **Remotion: não usado.** FFmpeg + legendas ASS cobrem cortes, silêncios, legenda tradicional, destaque, palavra a palavra, contorno e sombra, de forma mais leve e simples. Remotion só compensa para animações elaboradas (Fases 9+); também exige Chromium no servidor e pode exigir licença comercial conforme o porte da empresa. Reavaliamos na Fase 9.
2. **Banco e arquivos:** como você ainda não escolheu, começamos local (SQLite + disco). Migrar para Supabase (Postgres + armazenamento privado + login) é trocar `DATABASE_URL` e o módulo `storage.py`.
3. **Fila:** processamento em segundo plano dentro da própria API (2 tarefas ao mesmo tempo). Fila externa só se necessário.
4. **Hospedagem:** roda no seu computador. Online exige servidor com FFmpeg e disco (não serve hospedagem serverless).
5. **Transcrição:** `TRANSCRIBER=auto` usa a API da OpenAI se houver `OPENAI_API_KEY`; senão, Whisper local gratuito. Ambos implementados; nenhum testado com o Whisper real no ambiente de desenvolvimento.

## Dependências

Frontend: Next.js, React, TypeScript, Tailwind CSS. Backend: FastAPI, SQLAlchemy, FFmpeg, faster-whisper (local) e/ou OpenAI (API).

## Como cada fase foi implementada

- **Fase 2 (upload/prévia):** `POST /projects` grava o arquivo em `storage/projects/<id>/`, lê com FFprobe e gera miniatura. O vídeo só sai pela rota `/projects/<id>/video` (nunca pasta pública).
- **Fase 3 (transcrição):** `services/transcribe.py` (OpenAI ou local), palavras com tempo → `services/captions.py` agrupa em legendas (quebra em pausas > 0,5 s, ~34 caracteres ou 3,5 s).
- **Fase 4 (correção):** `PUT /projects/<id>/captions`. Se o texto/tempo de uma legenda muda, o tempo por palavra é redistribuído proporcionalmente.
- **Fase 5 (legendas no vídeo):** `services/ass.py` gera legendas ASS (zona segura, cores GM, contorno/sombra); `services/render.py` grava com FFmpeg.
- **Fase 6 (silêncios):** `silencedetect` do FFmpeg; `services/cuts.py` remove só o miolo da pausa (respiro de 0,25 s em cada ponta) e remapeia os tempos das legendas.
- **Fase 7 (estilos):** cada estilo é um conjunto de configurações em `web/src/lib/presets.ts` (sem lógica duplicada no servidor).
- **Fase 8 (exportação):** MP4 H.264 CRF 18, AAC 192k, 1080×1920; vídeos não verticais ganham fundo desfocado (nada é cortado, o produto fica inteiro).

## Preparado para as próximas fases

O render monta um grafo de filtros em etapas (`render.py`); zoom (Fase 9) entra como mais uma etapa antes do enquadramento, usando os mesmos tempos já mapeados. Remotion continua adiado.

## Antes de colocar online

1. Login (ex.: Supabase Auth) e filtro por `owner_id` em todas as rotas (a coluna já existe).
2. Armazenamento privado em nuvem com links temporários (hoje: disco local).
3. Limite de tamanho/tempo por usuário e fila de processamento se houver vários usuários.
