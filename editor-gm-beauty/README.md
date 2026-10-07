# Editor GM Beauty

Transforme vídeos brutos em conteúdo pronto para postar.

Fluxo: **upload → escolher tipo e estilo → edição automática → revisar → exportar** (MP4 H.264, 1080×1920, 9:16).

## O que já funciona (Fases 1–12, menos a 13)

- Dashboard com projetos (miniatura, status, duplicar, excluir permanente).
- Upload de MP4/MOV com barra de progresso.
- Transcrição em português com timestamps por palavra (Whisper).
- Detecção de pausas e remoção opcional (só o miolo das pausas longas; a fala continua natural).
- Legendas: tradicional, com palavras destacadas e palavra por palavra; cores GM; contorno e sombra leves; zona segura de Reels/TikTok.
- Correção de qualquer legenda (texto e tempos) antes de exportar.
- Estilos GM Clean, GM Viral, GM Produto e GM Oferta.
- Logo opcional (posição, tamanho e transparência).
- Exportação 9:16 e download.
- **Zoom automático** (Desligado / Sutil / Dinâmico): aproximações suaves e espaçadas, até 5% (sutil) ou 9% (dinâmico), sem mexer em logo e legendas. GM Produto vem com zoom desligado para o produto ficar inteiro e parado.
- **Efeitos sonoros + Biblioteca GM:** você envia seus próprios sons (Transição, Destaque, Oferta) em “Biblioteca”. O editor sugere onde colocar (início de zoom, palavra destacada, preço), com no mínimo 1,5 s entre efeitos e no máximo um a cada ~6 s. Você revisa a lista (remove, troca o som, adiciona manualmente), ajusta o volume (padrão −14 dB) e exporta. A prévia toca os efeitos. Confira a licença de cada som que enviar.
- **B-roll:** na Biblioteca você envia clipes seus (MP4/MOV) e escreve **como o produto é falado** em cada um (ex.: “base Ruby Rose, base da Ruby Rose”). O editor só sugere o clipe quando a fala cita esse nome: nunca nos primeiros 1,5 s, com 3 s de intervalo entre eles e no máximo 40% do vídeo coberto. O B-roll cobre a imagem e a sua fala continua. Você revisa a lista (troca o clipe, ajusta a duração, remove, adiciona) e a prévia mostra o resultado. GM Produto já vem com B-roll ligado.
- **Análise do gancho** dos primeiros 3 s: checa início rápido, abertura que chama a pessoa, legenda curta e destaque; oferece cortar o silêncio inicial e destacar a palavra do gancho. É uma checagem por regras sobre a transcrição (não é IA).

## Instalação no seu computador (passo a passo)

**1. Instale 3 programas (uma única vez)**

| Programa | Mac | Windows |
|---|---|---|
| Node.js (LTS) | https://nodejs.org | https://nodejs.org |
| Python **3.12** (recomendado; versões muito novas podem não instalar alguns componentes) | https://www.python.org/downloads | https://www.python.org/downloads/windows/ (marque **“Add python.exe to PATH”**) |
| FFmpeg 4.4 ou mais novo | instale o Homebrew (https://brew.sh) e rode `brew install ffmpeg` | no Prompt de Comando: `winget install ffmpeg` |

**2. Baixe o editor**

No GitHub (`gmbeauty/gmbeauty`), escolha o branch `claude/push-pending-commits-yvw5b6` (ou `main`, depois que o PR for aprovado), clique em **Code → Download ZIP** e extraia a pasta. A pasta que interessa é `editor-gm-beauty`.

**3. Abra o editor com dois cliques**

- **Mac:** dê dois cliques em `iniciar.command`. Se o Mac bloquear, clique com o botão direito → Abrir. Se disser que não tem permissão, abra o Terminal na pasta e rode `chmod +x iniciar.command`.
- **Windows:** dê dois cliques em `iniciar.bat`. (Se aparecer um aviso do Windows, “Mais informações → Executar assim mesmo”.)

Na primeira vez ele instala o que falta (alguns minutos, precisa de internet) e abre o navegador em **http://localhost:3000**. Nas próximas, abre em segundos. Para encerrar, feche a janela do terminal (no Windows, as duas janelas “Editor GM Beauty”).

> O iniciador de Mac/Linux foi testado. O `iniciar.bat` (Windows) foi escrito com cuidado, mas **não foi testado** em um Windows de verdade; se algo falhar, use os comandos manuais abaixo ou me avise com a mensagem que apareceu.

**Atalho na área de trabalho (sem janelas pretas)**

Depois que o `iniciar` funcionou uma vez, dê dois cliques em **`Criar atalho na area de trabalho`**. Ele cria na área de trabalho:
- **Editor GM Beauty**, com o ícone da GM: abre o editor em segundo plano e o navegador em **http://localhost:3000**, sem janelas pretas;
- **Parar Editor GM Beauty**: encerra o editor.

Se o editor demorar a abrir ou não abrir, ele mostra um aviso e abre a pasta `api\storage\logs` com o registro. Mantenha a pasta `editor-gm-beauty` onde está (de preferência fora de uma pasta sincronizada pelo OneDrive); os atalhos apontam para ela. Se mover a pasta, rode o `Criar atalho na area de trabalho` de novo.

> Estes scripts do Windows (`.vbs`) também **não foram testados** em um Windows de verdade.

**4. Transcrição (escolha uma)**

- **Gratuita (padrão):** nada a fazer. Na primeira transcrição o programa baixa o modelo Whisper (~500 MB), então a primeira vez demora.
- **Mais rápida, com a API da OpenAI (paga por uso):** crie na pasta `editor-gm-beauty` um arquivo de texto chamado `chave-openai.txt` com a sua chave dentro (só a chave) e abra o iniciador de novo.

**Seus vídeos ficam só no seu computador**, na pasta `api/storage` (não vai para o GitHub). Para fazer backup, copie essa pasta.

**Atualizar para uma versão nova:** baixe o ZIP de novo, extraia e copie a sua pasta `api/storage` antiga para dentro da nova.

## Comandos manuais (alternativa ao iniciador)

Requisitos: os mesmos 3 programas acima. Abra dois terminais. (No Windows use `py -3` no lugar de `python3` e `.venv\Scripts\activate` no lugar de `source .venv/bin/activate`.)

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

### Transcrição nos comandos manuais

- **Local e gratuita (padrão sem chave):** nada a configurar. Na 1ª vez baixa o modelo Whisper (~500 MB para `small`) e transcreve no seu computador. Para mais precisão: `WHISPER_MODEL=medium`.
- **API da OpenAI (mais rápida):** `export OPENAI_API_KEY=sua-chave` antes de iniciar o servidor.

Variáveis opcionais do servidor: `CAPTION_FONT` (fonte das legendas no vídeo; precisa estar instalada, padrão `Arial`), `CAPTION_FONTS_DIR` (pasta com fontes extras), `DATA_DIR` (onde ficam os vídeos), `DATABASE_URL` (PostgreSQL/Supabase), `MAX_UPLOAD_MB`.

## Se a transcrição falhar

Dê dois cliques em **`diagnostico`** (na pasta do editor). Ele testa, passo a passo, o FFmpeg, o componente de transcrição, a internet e o download do modelo de voz, e mostra o que falhou. Tire um print da janela e envie para quem está ajudando. Causas comuns: internet instável ou bloqueando o download do modelo (tente outra rede, como o hotspot do celular, e desligue VPN/antivírus) e falta do “Microsoft Visual C++” (https://aka.ms/vs/17/release/vc_redist.x64.exe). Para um download menor, defina `WHISPER_MODEL=base`.

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

Ainda não feita: IA analisando roteiro e retenção (Fase 14, exigiria uma chave de API paga). Música automática (Fase 13) está fora do plano: contas comerciais têm restrição de música; o mais seguro é escolher a faixa dentro do Instagram/TikTok ao postar.

Veja `ARCHITECTURE.md` para as decisões técnicas.
