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
- Todas as chamadas do frontend passam por `web/src/lib/api.ts`. Na Fase 1 ela devolve dados fictícios; nas próximas fases passa a chamar a API, sem reescrever as telas.

## Pipeline (Fases 3–8)

Upload → extrair áudio → transcrever (timestamps por palavra) → detectar silêncios → sugerir cortes → montar legendas → aplicar preset → renderizar → MP4 1080×1920 H.264.
Cada etapa é uma função em `api/app/services/`, para testar e trocar uma sem mexer nas outras.

## Estrutura de pastas

```
editor-gm-beauty/
├── ARCHITECTURE.md, README.md
├── web/src/
│   ├── app/            páginas: / , /novo , /editor/[id]
│   ├── components/     peças visuais; components/editor/ = tela do editor
│   └── lib/            tipos, presets, tipos de conteúdo, safe zone, mock-data, api
└── api/app/
    ├── main.py         entrada da API
    ├── routers/        rotas HTTP
    └── services/       ffmpeg, transcrição, legendas, silêncios
```

## Banco de dados (planejado, Fase 2)

- `projects`: id, owner_id, nome, status, tipo de conteúdo, estilo, duração, caminhos dos arquivos, datas.
- `caption_segments`: project_id, início, fim, texto, palavras em destaque.
- `silences`: project_id, início, fim.
- `dictionary_terms` (futuro): owner_id, termo, correção.
- Toda tabela tem `owner_id`; regras de acesso garantem que cada vídeo pertence só à sua conta.

## Privacidade e exclusão

Arquivos ficam em armazenamento **privado** (nunca URL pública; acesso por link temporário assinado). Excluir um projeto apaga o registro e todos os arquivos (original, áudio, exportado).

## Erros

O usuário vê mensagens simples ("Não conseguimos processar este vídeo. Tente novamente."). O detalhe técnico (saída do FFmpeg etc.) é gravado em log/campo interno do projeto, nunca na tela.

## Decisões e pontos para validar

1. **Remotion: não usar no MVP.** FFmpeg + legendas no formato ASS cobrem cortes, silêncios, legenda tradicional, destaque, palavra a palavra, contorno e sombra, de forma mais leve e simples. Remotion só compensa para animações elaboradas (Fases 9+); também exige Chromium no servidor e pode exigir licença comercial conforme o porte da empresa. Reavaliamos na Fase 9.
2. **Supabase vs PostgreSQL puro:** recomendo Supabase (Postgres + login + armazenamento privado no mesmo lugar). Não muda a stack, só a hospedagem.
3. **Fila de processamento:** adiada. Primeiro, processamento em segundo plano simples na própria API; fila só se necessário.
4. **Hospedagem da API:** precisa de servidor com FFmpeg e disco (não serve hospedagem serverless). A decidir antes da Fase 2.
5. **Transcrição:** Whisper via API da OpenAI (simples, pago por minuto) ou local (gratuito, mais pesado). A decidir antes da Fase 3.

## Dependências (Fase 1)

Next.js, React, TypeScript, Tailwind CSS. Backend: FastAPI + Uvicorn (esqueleto).
Previstas: FFmpeg, Whisper, PostgreSQL/Supabase.
